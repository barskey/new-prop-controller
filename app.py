from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import defaults
import time

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


posx, posy = 20, 20  # starting position of graph nodes


SEND_LENGTH = 250  # number of characters to send as publish event (actually is SEND_LENGTH+1 since it starts at 0)

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
		name = data['name']
		inputs.append({'cid': cid, 'name': name})
		outputs.append({'cid': cid, 'name': name, 'port': 'A'})
		outputs.append({'cid': cid, 'name': name, 'port': 'B'})
		outputs.append({'cid': cid, 'name': name, 'port': 'C'})
		outputs.append({'cid': cid, 'name': name, 'port': 'D'})
	return render_template('dashboard.html', async_mode=socketio.async_mode, inputs=inputs, outputs=outputs)


@socketio.on('connect')
def connect():
	#print('Logging in to Particle...')
	username = 'barskey@gmail.com'
	pwd = 'CarlyAnn1102'
	emit('log_response', {'response': 'Connecting to Particle...', 'style': 'warning'})
	emit('get_token', {'username': username, 'pwd': pwd})


@socketio.on('got_devices')
def got_devices(msg):
	devices = msg['data']['body']
	for controller in devices:
		cid = controller['id']
		controllers = json.load(open('data/controllers.json'))  # get existing controllers
		hexids = list()
		cids = set()
		for hexid,details in controllers.items():
			hexids.append(hexid)
			cids.add(details['hexid'])
		if cid not in cids:
			controllers[cid] = defaults.CONTROLLER  # add to existing controllers
			controllers[cid]['name'] = controller['name']
			new_hex_id = get_next_hexid(hexids)
			controllers[cid]['hexid'] = new_hex_id
			with open('data/controllers.json', 'w') as outfile:  # write to file
				json.dump(controllers, outfile)
			# socketio.emit('add_controller, {}')
			print('Controller id:{0} hexid:{1} added.'.format(cid, new_hex_id))


@socketio.on('show_graph')
def load_graph():
	#print('Logged in.')
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
	controllers = json.load(open('data/controllers.json'))  # get existing controllers
	global posx, posy
	cid = msg.get('cid', '')
	op = None
	if msg['type'] == 'input':
		op = defaults.TRIGGERS[msg['type']]
		op['properties']['title'] = 'Trigger: ' + controllers[cid]['name']
	elif msg['type'] in ['interval', 'random', 'timer']:
		op = defaults.TRIGGERS[msg['type']]
	elif msg['type'] == 'output':
		op = defaults.ACTIONS[msg['type']]
		op['properties']['title'] = controllers[cid]['name'] + ' > ' + msg['port']
	else:
		print(msg['type'], msg)
		return
	op['top'] = posy
	op['left'] = posx
	opid = get_next_opid()
	hexid = controllers.get('cid').get('hexid', '') if controllers.get('cid') else ''
	update_params({
		'opid': str(opid),
		'hexid': hexid,
		'title': op['properties']['title'],
		'type': msg['type']
		})
	emit('add_to_graph', {'data': op, 'opid': opid})
	posx = posx + 20
	posy = posy + 20


@socketio.on('update_parameters')
def update_params(msg):
	# msg = {opid: ##, title: sss, param1: sss, param2: sss, type: sss}
	opid = None
	try:
		opid = msg['opid'].decode('utf-8')
	except AttributeError:
		opid = msg['opid']
	params = json.load(open('data/params.json'))
	# NOTE - all operator types get param1 and param2 set, even if they are not using it, e.g. outputs
	params[opid] = {
		'hexid': msg.get('hexid'),
		'title': msg.get('title', 'No Name'),
		'param1': msg.get('param1', 5),  # default to 5s if not set
		'param2': msg.get('param2', 10),  # default to 10s if not set
		'type': msg.get('type', '')  # default to empty string if not set
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
	key = None
	try:
		key = msg['key'].decode('utf-8')
	except AttributeError:
		key = msg['key']
	value = msg['val']
	controllers = json.load(open('data/controllers.json'))
	if key == 'name':
		controllers[cid][key] = value
	else:
		controllers[cid][key] = '1' if value else '0'
	with open('data/controllers.json', 'w') as outfile:
		json.dump(controllers, outfile)
	strDefaults = controllers[cid]['hexid'] + controllers[cid]['input'] + controllers[cid]['A'] + controllers[cid]['B'] + controllers[cid]['C'] + controllers[cid]['D']
	emit('send_defaults', {'data': strDefaults, 'cid': cid})
	emit('log_response', {'response': 'Saved controller settings.', 'style': 'success'})


@socketio.on('get_op_params')
def get_params(msg):
	params = json.load(open('data/params.json'))
	emit('show_params', {
		'params': params[str(msg['opid'])],
		'opid': str(msg['opid'])
		}
	)


@socketio.on('save_graph')
def save_to_file(msg):
	with open('data/graph.json', 'w') as outfile:
		json.dump(msg['data'], outfile)


@socketio.on('delete_op_params')
def delete_params(msg):
	opid = str(msg['opid'])
	params = json.load(open('data/params.json'))
	if params.get(opid, None) is not None:
		del params[opid]
		with open('data/params.json', 'w') as outfile:
			json.dump(params, outfile)


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


# Parse graph json data into json representation of action/event data to send to controllers.
# See defaults.py for dict structure.
# triggers - each trigger sent as JSON:
# {cid: <contoller id>,
#  t(type): <R(random), (V)interval, (I)input>,
#  p(params): [<param1, param2>],
#  a(actions): []
# }
# a(actions) - an array of objects like:
# [ {cid: <controller id>,
#    t(type): <O(output), T(timer), S(sound)>,
#    p(params): <A(port name), ##(sound id), #.#(time in s)>,
#    a(actions): []
# } ]
@socketio.on('parse_graph')
def parse_graph_data():
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data['operators']
	#links = data['links']
	#print (json.dumps(links, indent=2))

	triggers = []

	# First find all operators of type interval, random or trigger - these are required to trigger other actions.
	for str_id, v in operators.items():
		int_id = int(str_id)
		if v['properties']['class'] == 'trigger-interval':
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				't': 'V',
				'p': [params[str_id]['param1']]
			})
		elif v['properties']['class'] == 'trigger-random':
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				't': 'R',
				'p': [params[str_id]['param1'], params[str_id]['param2']]
			})
		elif v['properties']['class'] == 'trigger-input':
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				't': 'I',
				'p': [params[str_id]['param1']]
			})

	# iterate through triggers and build action arrays
	for trigger in triggers:
		#print ('Getting actions for op ' + params[id]['title'])
		trigger['a'] = get_actions(str(trigger['opid']))

	#print (json.dumps(triggers, indent=2))
	print ('String length: {0}'.format(len(json.dumps(triggers, separators=(',',':')))))

	data = json.dumps(triggers, separators=(',', ':'))  # TODO Get rid of all opid keys to save space
	#print('Sending Trigger:', data)
	emit('send_graph', {'data': data})


def get_next_opid():
	i = 0
	ops = json.load(open('data/graph.json')).get('operators', None)
	if ops is None:
		return i
	while ops.get(str(i), None) is not None:
		i = i + 1
	return i


def get_next_hexid(hexid_list):
	i = 1
	hexid = format(i, '02x') # 2-digit hex string

	while hexid in sorted(hexid_list):
		print('Checking hexid ' + hexid)
		i = i + 1
		hexid = format(i, '02x')

	return hexid


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
