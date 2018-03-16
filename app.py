from threading import Lock
from flask import Flask, render_template, session, request, url_for
from flask_socketio import SocketIO, emit
import json, random
import defaults

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

posx, posy = 20, 20 # starting position of graph nodes

def background_thread():
	"""Example of how to send server generated events to clients."""
	count = 0
	while True:
		socketio.sleep(10)
		count += 1
		print ('emitting my_response')
		socketio.emit('my_response', {'data': 'Server generated event', 'count': count})


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
def test_connect():
	print ('connect')
	#global thread
	#with thread_lock:
	#	if thread is None:
	#		thread = socketio.start_background_task(target=background_thread)
	#emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('connected')
def connected():
	print ('connected')
	data = json.load(open('data/graph.json'))
	emit('create_graph', {'data': data})


@socketio.on('my_broadcast_event')
def test_broadcast_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my_response',
		 {'data': message['data'], 'count': session['receive_count']},
		 broadcast=True)


@socketio.on('ping_received')
def controller_connected(msg):
	cid = msg['data'].decode('utf-8')
	controllers = json.load(open('data/controllers.json')) # get existing controllers
	if controllers.get(cid, None) is None:
		controllers[cid] = defaults.CONTROLLER # add to existing controllers
		with open('data/controllers.json', 'w') as outfile: # write to file
			json.dump(controllers, outfile)
		#socketio.emit('add_controller, {}')
		print ('Controller added.')


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
		print (msg['type'], msg)
		return
	op['top'] = posy
	op['left'] = posx
	id = get_next_opid()
	update_params({'opid': str(id), 'title': op['properties']['title'], 'type': msg['type']})
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
	p['title'] = msg.get('title', 'No Name')
	p['param1'] = msg.get('param1', 5) # default to 5s if not set
	p['param2'] = msg.get('param2', 10) # default to 10s if not set
	p['type'] = msg.get('type', '') # default to empty string if not set
	params = json.load(open('data/params.json'))
	# NOTE - all operator types get param1 and param2 set, even if they are not using it, e.g. outputs
	params[id] = {'title': p['title'], 'param1': p['param1'], 'param2': p['param2'], 'type': p['type']}
	with open('data/params.json', 'w') as outfile:
		json.dump(params, outfile)


@socketio.on('update_controller')
def update_controller(msg):
	cid = msg['cid'].decode('utf-8')
	port = msg['port'].decode('utf-8')
	state = msg['val']
	controllers = json.load(open('data/controllers.json'))
	controllers[cid][port] = 'HI' if state else 'LO'
	with open('data/controllers.json', 'w') as outfile:
		json.dump(controllers, outfile)


@socketio.on('get_op_params')
def get_params(msg):
	params = json.load(open('data/params.json'))
	emit('show_params', {'params': params[str(msg['id'])], 'opid': str(msg['id'])})


@socketio.on('save_graph')
def save_to_file(msg):
	with open('data/graph.json', 'w') as outfile:
		json.dump(msg['data'], outfile)


@socketio.on('delete_op_params')
def delete_params(msg):
	id = str(msg['id'])
	params = json.load(open('data/params.json'))
	print('Before delete:', params)
	if params.get(id, None) is not None:
		del params[id]
		print('After delete:', params)
		with open('data/params.json', 'w') as outfile:
			json.dump(params, outfile)
		
def makeDict(array):
	obj = {}
	for item in array:
		obj[item['name']] = item['value']
	return obj

	
@socketio.on('clear_data')
def clear_data(msg):
	print (msg['data'])
	empty = {}
	if msg['data'] in ['graph', 'all']:
		with open('data/graph.json', 'w') as outfile:
			json.dump(empty, outfile)
		with open('data/params.json', 'w') as outfile:
			json.dump(empty, outfile)
	if msg['data'] == 'all':
		pass
		#with open('data/controllers', 'w') as outfile:
		#	json.dump(empy, outfile)

def get_next_opid():
	i = 0
	ops = json.load(open('data/graph.json')).get('operators', None)
	if ops is None:
		return i
	while ops.get(str(i), None) is not None:
		i = i + 1
	return i


if __name__ == '__main__':
	socketio.run(app, debug=True)
