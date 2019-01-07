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
	for hexid, data in json.load(open('data/controllers.json')).items():
		if data['type'] == 'Node': # only collect inputs and outputs for Nodes
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

@socketio.on('clone_op')
def clone_op(msg):
	params = json.load(open('data/params.json'))
	opid = get_next_opid()
	old_opid = str(msg['opid'])
	op = msg['op']
	op['top'] = op['top'] + 10
	op['left'] = op['left'] + 10
	update_params({
		'opid': str(opid),
		'hexid': params[old_opid]['hexid'],
		'title': params[old_opid]['title'],
		'type': params[old_opid]['type'],
		'param1': params[old_opid]['param1'],
		'param2': params[old_opid]['param2'],
		'param3': params[old_opid]['param3']
	})
	emit('add_to_graph', {'data': op, 'opid': opid})



@socketio.on('update_parameters')
def update_params(msg):
	# msg = {opid: ##, title: sss, param1: sss, param2: sss, type: sss}
	opid = str(msg['opid'])
	params = json.load(open('data/params.json'))
	# NOTE - all operator types get param1/2/3 set, even if they are not using it, e.g. outputs
	params[opid] = {
		'hexid': msg.get('hexid'),
		'title': msg.get('title', 'No Name'),
		'param1': msg.get('param1', 5),  # default to 5s if not set
		'param2': msg.get('param2', 10),  # default to 10s if not set
		'param3': msg.get('param3', 0),  # default to 0s if not set
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
	opid = str(msg['opid'])
	controllers = json.load(open('data/controllers.json'))
	params = json.load(open('data/params.json'))
	hexid = params[opid]['hexid']
	info = []
	if params[opid]['type'] == 'interval':
		info.append('This Interval happens continously every ' + str(params[opid]['param1']) + ' seconds.')
		info.append('After every ' + str(params[opid]['param1']) + ' seconds the connected outputs will run.')
	elif params[opid]['type'] == 'random':
		info.append('This Interval happens continously between ' + str(params[opid]['param1']) + ' and ' + str(params[opid]['param2']) + ' seconds.')
		info.append('The connected actions will run and a new random delay will be used.')
	elif params[opid]['type'] == 'output':
		info.append('Controller: ' + controllers[hexid]['name'])
		info.append(' Port: ' + str(params[opid]['param2']))
	elif params[opid]['type'] == 'input':
		info.append('Controller: ' + controllers[hexid]['name'])
		info.append('')
	emit('show_params', {
		'params': params[opid],
		'opid': opid,
		'info': info
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
# See defaults.py for operators/links dict structure.
# triggers - each trigger sent as JSON:
# {hexid: <hex id>,
#  type: <Random, Interval, Input>,
#  params: [<param1, param2>],
#  actions: []
# }
@socketio.on('parse_graph')
def parse_graph_data():
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
			#  Look for links that come from this trigger.
			#  Loop thru links twice to check for h and l connecters.
			for linkid,link in links.items():
				if str(link['fromOperator']) == str_id and link['fromConnector'] == 'h':
					triggers.append({
						'opid': str_id,
						'hexid': params[str_id]['hexid'],
						'type': 'Input',
						'params': ['h']
					})
					break #  only append this trigger once
			for linkid,link in links.items():
				if str(link['fromOperator']) == str_id and link['fromConnector'] == 'l':
					triggers.append({
						'opid': str_id,
						'hexid': params[str_id]['hexid'],
						'type': 'Input',
						'params': ['l']
					})
					break #  only append this trigger once

	# iterate through triggers and build action arrays
	for trigger in triggers:
		#print('Getting actions for trigger ' + trigger['type'], trigger)
		trigger['actions'] = get_actions(str(trigger['opid']), trigger['type'], trigger['params'][0])
		trigger.pop('opid') #  remove 'opid' key so it doesn't take more chars in output

	print (json.dumps(triggers, indent=2))

	data = json.dumps(triggers, separators=(',', ':'))
	#data = json.dumps(triggers, separators=(',', ':')).replace('"', '')
	print ('String length: {0}'.format(len(data)))
	# TODO Get rid of all opid keys to save space
	# TODO Remove all "" from string to see if it still parses
	#print('Sending Trigger:', data)
	emit('send_graph', {'data': data})


# returns actions[] - an array of objects like:
# [ {hexid: <hex id>,
#    type: <Output, Timer, Sound>,
#    params: [<H/L(state), ##(sound id), #.#(time in s)>, <>], <-- if output, [0] is state, [1] is port
#    actions: []
# } ]
def get_actions(str_opid, from_type, trigger_state):
	params = json.load(open('data/params.json'))
	data = json.load(open('data/graph.json'))
	operators = data['operators']
	links = data['links']

	actions = []
	for linkid, v in links.items():
		if str_opid == str(v['fromOperator']):  # matched this operator to from trigger/action
			#print(from_type, v['fromConnector'], on_state)
			# if this was called from a trigger, only proceed if from connector matches
			if from_type == "Input" and v['fromConnector'] != trigger_state:
				break
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
			action = {'hexid': hexid, 'type': type, 'params': action_params}
			action['actions'] = get_actions(str(to_opid), 'Action', v['fromConnector'])
			#  add a timer action if this is an input and needs a delay before
			#print(type,params[str(to_opid)]['param3'])
			if type == 'Output' and float(params[str(to_opid)]['param3']) > 0:
				t_action = {
					'hexid': '',
					'type': 'Timer',
					'params': [params[str(to_opid)]['param3']],
					'actions': [action]
				}
				actions.append(t_action)
			else:
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
