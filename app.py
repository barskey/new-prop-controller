from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import defaults

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


posx, posy = 20, 20  # starting position of graph nodes


@app.route('/')
def index():
	controllers = json.load(open('data/controllers.json'))
	return render_template('controllers.html', controllers=controllers)


@app.route('/dashboard')
def dashboard():
	global posx, posy
	posx, posy = 20, 20
	inputs = []
	outputs = []
	for cid, data in json.load(open('data/controllers.json')).items():
		inputs.append(cid)
		outputs.append(cid + '-A')
		outputs.append(cid + '-B')
		outputs.append(cid + '-C')
		outputs.append(cid + '-D')
	return render_template('dashboard.html', async_mode=socketio.async_mode, inputs=inputs, outputs=outputs)


@socketio.on('connect')
def connect():
	print ('connect')
	username = 'barskey@gmail.com'
	pwd = 'CarlyAnn1102'
	emit('log_response', {'response': 'Connecting to Particle...'})
	emit('get_token', {'username': username, 'pwd': pwd})


@socketio.on('show_graph')
def load_graph():
	print('connected')
	data = json.load(open('data/graph.json'))
	emit('create_graph', {'data': data})


@socketio.on('ping_received')
def controller_connected(msg):
	cid = msg['data'].decode('utf-8')
	controllers = json.load(open('data/controllers.json'))  # get existing controllers
	if controllers.get(cid, None) is None:
		controllers[cid] = defaults.CONTROLLER  # add to existing controllers
		with open('data/controllers.json', 'w') as outfile:  # write to file
			json.dump(controllers, outfile)
		# socketio.emit('add_controller, {}')
		print('Controller added.')


@socketio.on('add_op')
def add_op(msg):
	global posx, posy
	op = None
	if msg['type'] == 'input':
		op = defaults.TRIGGERS[msg['type']]
		op['properties']['title'] = 'Input -> ' + msg['cid']
	elif msg['type'] in ['interval', 'random', 'timer']:
		op = defaults.TRIGGERS[msg['type']]
	elif msg['type'] == 'output':
		op = defaults.ACTIONS[msg['type']]
		op['properties']['title'] = 'Output -> ' + msg['cid']
	else:
		print(msg['type'], msg)
		return
	op['top'] = posy
	op['left'] = posx
	id = get_next_opid()
	update_params({
		'opid': str(id),
		'title': op['properties']['title'],
		'type': msg['type']
		})
	emit('add_to_graph', {'data': op, 'id': id})
	posx = posx + 20
	posy = posy + 20


@socketio.on('update_parameters')
def update_params(msg):
	# msg = {opid: ##, title: sss, param1: sss, param2: sss, type: sss}
	id = None
	try:
		id = msg['opid'].decode('utf-8')
	except AttributeError:
		id = msg['opid']
	p = {}
	p['cid'] = 'C123'
	p['title'] = msg.get('title', 'No Name')
	p['param1'] = msg.get('param1', 5)  # default to 5s if not set
	p['param2'] = msg.get('param2', 10)  # default to 10s if not set
	p['type'] = msg.get('type', '')  # default to empty string if not set
	params = json.load(open('data/params.json'))
	# NOTE - all operator types get param1 and param2 set, even if they are not using it, e.g. outputs
	params[id] = {
		'cid': p['cid'],
		'title': p['title'],
		'param1': p['param1'],
		'param2': p['param2'],
		'type': p['type']
	}
	with open('data/params.json', 'w') as outfile:
		json.dump(params, outfile)


@socketio.on('update_controller')
def update_controller(msg):
	cid = None
	try:
		cid = msg['cid'].decode('utf-8')
	except AttributeError:
		cid = msg['cid']
	port = None
	try:
		port = msg['port'].decode('utf-8')
	except AttributeError:
		port = msg['port']
	state = msg['val']
	controllers = json.load(open('data/controllers.json'))
	controllers[cid][port] = '1' if state else '0'
	with open('data/controllers.json', 'w') as outfile:
		json.dump(controllers, outfile)
	strDefaults = controllers[cid]['input'] + controllers[cid]['A'] + controllers[cid]['B'] + controllers[cid]['C'] + controllers[cid]['D']
	emit('send_defaults', {'data': strDefaults, 'cid': cid})


@socketio.on('get_op_params')
def get_params(msg):
	params = json.load(open('data/params.json'))
	emit('show_params', {
		'params': params[str(msg['id'])],
		'opid': str(msg['id'])
		}
	)


@socketio.on('save_graph')
def save_to_file(msg):
	with open('data/graph.json', 'w') as outfile:
		json.dump(msg['data'], outfile)


@socketio.on('delete_op_params')
def delete_params(msg):
	id = str(msg['id'])
	params = json.load(open('data/params.json'))
	if params.get(id, None) is not None:
		del params[id]
		with open('data/params.json', 'w') as outfile:
			json.dump(params, outfile)


def makeDict(array):
	obj = {}
	for item in array:
		obj[item['name']] = item['value']
	return obj


@socketio.on('clear_data')
def clear_data(msg):
	print(msg['data'])
	empty = {}
	if msg['data'] in ['graph', 'all']:
		with open('data/graph.json', 'w') as outfile:
			json.dump(empty, outfile)
		with open('data/params.json', 'w') as outfile:
			json.dump(empty, outfile)
	if msg['data'] == 'all':
		pass
		# with open('data/controllers', 'w') as outfile:
		#	json.dump(empy, outfile)


def get_next_opid():
	i = 0
	ops = json.load(open('data/graph.json')).get('operators', None)
	if ops is None:
		return i
	while ops.get(str(i), None) is not None:
		i = i + 1
	return i


# Parse graph json data into json representation of action/event data to send to controllers.
# See defaults.py for dict structure.
# First find all operators of type interval, random or trigger - these are required to trigger other actions.
# Then build output structure in the form:
# triggers
# {<from opid>: {cid: <contoller id>,
#                t(type): <R(random), (V)interval, (I)input>
#                p(params): [<param1, param2>]
#                a(actions): []}}
# actions
# {<from opid>: {cid: <controller id>,
#                t(type): <O(output), T(timer), S(sound)>,
#                p(params): <A(port name), ##(sound id), #.#(time in s)>,
#                a(actions): []}}
@socketio.on('parse_graph')
def parse_graph_data():
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data['operators']
	#links = data['links']
	#print (json.dumps(links, indent=2))

	triggers = {}

	for str_id, v in operators.items():
		int_id = int(str_id)
		if v['properties']['class'] == 'trigger-interval':
			triggers[int_id] = {'cid': params[str_id]['cid'], 't': 'V', 'p': [params[str_id]['param1']]}
		elif v['properties']['class'] == 'trigger-random':
			triggers[int_id] =  {
				'cid': params[str_id]['cid'],
				't': 'R',
				'p': [params[str_id]['param1'], params[str_id]['param2']]
			}
		elif v['properties']['class'] == 'trigger-input':
			triggers[int_id] = {
				'cid': params[str_id]['cid'],
				't': 'I',
				'p': [params[str_id]['param1']]
			}

	# iterate through triggers and build action arrays
	for int_id, v in triggers.items():
		#print ('Getting actions for op ' + params[id]['title'])
		v['a'] = get_actions(str(int_id))

	#print (json.dumps(triggers, indent=2))
	#print ('String length: {0}'.format(len(json.dumps(triggers, separators=(',',':')))))

	part = 1
	for trigger_op_id, trigger in triggers.items():
		print('Sending Trigger:', trigger)
		emit('send_graph', {'part': str(part), 'data': json.dumps(trigger, separators=(',', ':')), 'complete': False})
		part = part + 1
	emit('send_graph', {'part': '', 'data': '', 'complete': True})


def get_actions(str_opid):
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data['operators']
	links = data['links']

	actions = []
	#links_copy = dict(links) # copy dict so as we iterate thru we can remove from original dict
	for linkid, v in links.items():
		from_opid = v['fromOperator']
		if str(from_opid) == str_opid:
			#del links[from_id] # remove it since we have already added to triggers
			to_opid = v['toOperator']  # operator id to which this link connects
			#print ('Found link connecting from {0} to {1}'.format(params[from_opid]['title'], params[to_opid]['title']))
			cid = params[str(to_opid)]['cid']  # get actual contoller id
			type = operators[str(to_opid)]['properties']['class']
			if type.endswith('timer'):
				type = 'T'
			elif type.endswith('output'):
				type = 'O'
			elif type.endswith('sound'):
				type = 'S'
			param = v['toConnector']
			action = {'opid': to_opid, 'cid': cid, 't': type, 'p': [param]}
			action['a'] = get_actions(str(to_opid))
			actions.append(action)

	return actions


if __name__ == '__main__':
	socketio.run(app, debug=True)
