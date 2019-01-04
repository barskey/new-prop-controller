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
	for hexid, data in json.load(open('data/controllers.json')).items():
		name = data['name']
		inputs.append({'hexid': hexid, 'name': name})
		outputs.append({'hexid': hexid, 'name': name, 'port': 'A'})
		outputs.append({'hexid': hexid, 'name': name, 'port': 'B'})
		outputs.append({'hexid': hexid, 'name': name, 'port': 'C'})
		outputs.append({'hexid': hexid, 'name': name, 'port': 'D'})
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
			cids.add(details['cid'])
		if cid not in cids:
			new_hex_id = get_next_hexid(hexids)
			controllers[new_hex_id] = defaults.CONTROLLER  # add to existing controllers
			controllers[new_hex_id]['name'] = controller['name']
			controllers[new_hex_id]['cid'] = cid
			controllers[new_hex_id]['type'] = 'Node' if controller['platform_id'] == 14 else 'Gateway'
			with open('data/controllers.json', 'w') as outfile:  # write to file
				json.dump(controllers, outfile)
			# socketio.emit('add_controller, {}')
			print('Controller id:{0} hexid:{1} added.'.format(cid, new_hex_id))


@socketio.on('show_graph')
def load_graph():
	#print('Logged in.')
	data = json.load(open('data/graph.json'))
	emit('create_graph', {'data': data})


@socketio.on('add_op')
def add_op(msg):
	controllers = json.load(open('data/controllers.json'))  # get existing controllers
	global posx, posy
	hexid = msg.get('hexid', '')
	op = None
	param2 = 10  # default if param is not set
	if msg['type'] == 'input':
		op = defaults.TRIGGERS[msg['type']]
		op['properties']['title'] = 'Trigger: ' + controllers[hexid]['name']
	elif msg['type'] in ['interval', 'random', 'timer']:
		op = defaults.TRIGGERS[msg['type']]
	elif msg['type'] == 'output':
		op = defaults.ACTIONS[msg['type']]
		op['properties']['title'] = controllers[hexid]['name'] + ' > ' + msg['port']
		param2 = msg['port']
	else:
		print(msg['type'], msg)
		return
	op['top'] = posy
	op['left'] = posx
	opid = get_next_opid()
	update_params({
		'opid': str(opid),
		'hexid': hexid,
		'title': op['properties']['title'],
		'type': msg['type'],
		'param2': param2
		})
	emit('add_to_graph', {'data': op, 'opid': opid})
	posx = posx + 20
	posy = posy + 20


@socketio.on('update_parameters')
def update_params(msg):
	# msg = {opid: ##, title: sss, param1: sss, param2: sss, type: sss}
	opid = str(msg['opid'])
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
	hexid = str(msg['hexid'])
	key = str(msg['key'])
	value = msg['val']
	controllers = json.load(open('data/controllers.json'))
	if key == 'name':
		controllers[hexid][key] = value
		print('set name')
	else:
		#  Dont send defaults to controllers for name change only
		controllers[hexid][key] = '1' if value else '0'
		strDefaults = hexid + controllers[hexid]['input'] + controllers[hexid]['A'] + controllers[hexid]['B'] + controllers[hexid]['C'] + controllers[hexid]['D']
		emit('send_defaults', {'data': strDefaults, 'cid': controllers[hexid]['cid']})
		emit('log_response', {'response': 'Saved controller settings.', 'style': 'success'})
		print('emit send_defaults')
	with open('data/controllers.json', 'w') as outfile:
		json.dump(controllers, outfile)


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
	#print('Clearing graph.', msg['data'])
	with open('data/graph.json', 'w') as outfile:
		json.dump(msg['data'], outfile)
	with open('data/params.json', 'w') as outfile:
		json.dump({}, outfile)


# Parse graph json data into json representation of action/event data to send to controllers.
# See defaults.py for dict structure.
# triggers - each trigger sent as JSON:
# {hexid: <hex id>,
#  type: <Random, Interval, Input>,
#  params: [<param1, param2>],
#  actions: []
# }
links = None
@socketio.on('parse_graph')
def parse_graph_data():
	global links
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data.get('operators', None)
	if operators is None:
		return
	links = data.get('links', None)
	#print (json.dumps(links, indent=2))

	triggers = []

	# First find all operators of type interval, random or trigger - these are required to trigger other actions.
	for str_id, v in operators.items():
		type = v['properties']['class']
		if type.endswith('interval'):
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				'type': 'Interval',
				'params': [str(params[str_id]['param1'])]
			})
		elif type.endswith('random'):
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				'type': 'Random',
				'params': [str(params[str_id]['param1']), str(params[str_id]['param2'])]
			})
		elif type.endswith('input'):
			# create two triggers - one for on hi, one for on lo
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				'type': 'Input',
				'params': ['h']  # on HI
			})
			triggers.append({
				'opid': str_id,
				'hexid': params[str_id]['hexid'],
				'type': 'Input',
				'params': ['l']  # on LO
			})

	# iterate through triggers and build action arrays
	for trigger in triggers:
		#print('Getting actions for trigger ' + trigger['type'], trigger)
		trigger['actions'] = get_actions(str(trigger['opid']), trigger['type'], trigger['params'][0])

	#print (json.dumps(triggers, indent=2))
	print ('String length: {0}'.format(len(json.dumps(triggers, separators=(',',':')))))

	data = json.dumps(triggers, separators=(',', ':'))  # TODO Get rid of all opid keys to save space
	#print('Sending Trigger:', data)
	emit('send_graph', {'data': data})


# returns actions[] - an array of objects like:
# [ {hexid: <hex id>,
#    type: <Output, Timer, Sound>,
#    params: [<H/L(state), ##(sound id), #.#(time in s)>, <>], <-- if output, [0] is state, [1] is port
#    actions: []
# } ]
def get_actions(str_opid, from_type, on_state):
	global links
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data['operators']
	#links = data['links']

	actions = []
	links_copy = dict(links) # copy dict so as we iterate thru we can remove from original dict
	for linkid, v in links_copy.items():
		if str_opid == str(v['fromOperator']):  # matched this operator to from trigger/action
			proceed = True
			#print(from_type, v['fromConnector'], on_state)
			if from_type == "Input":  # if this is a trigger...
				if v['fromConnector'] != on_state:  # only proceed if from connector matches
					proceed = False
			if proceed is True:
				del links[linkid] # remove it since we have already added to triggers
				to_opid = v['toOperator']  # operator id to which this link connects
				hexid = params[str(to_opid)]['hexid']  # get hex id of controller
				type = operators[str(to_opid)]['properties']['class']
				action_params = []
				if type.endswith('timer'):
					type = 'Timer'
					action_params = [str(params[str(to_opid)]['param1'])]
				elif type.endswith('output'):
					type = 'Output'
					action_params = [v['toConnector'], params[str(to_opid)]['param2']]
				elif type.endswith('sound'):
					action_params = []
					type = 'Sound'
				action = {'opid': to_opid, 'hexid': hexid, 'type': type, 'params': action_params}
				action['actions'] = get_actions(str(to_opid), 'Action', v['fromConnector'])
				actions.append(action)

	#print('Found actions:', actions)
	return actions


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


if __name__ == '__main__':
	socketio.run(app, debug=True)
