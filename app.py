from threading import Lock
from flask import Flask, render_template, session, request, url_for
from flask_socketio import SocketIO, emit
import json

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
	triggers = {}
	actions = {}
	data = {}
	inputs = []
	for c in json.load(open('data/controllers.json')):
		inputs.append((c['id']))
	return render_template('dashboard.html', async_mode=socketio.async_mode, triggers=triggers, actions=actions, inputs=inputs, graphData=data)

@socketio.on('my_event')
def test_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my_response',
		 {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event')
def test_broadcast_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my_response',
		 {'data': message['data'], 'count': session['receive_count']},
		 broadcast=True)


@socketio.on('disconnect_request')
def disconnect_request():
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my_response',
		 {'data': 'Disconnected!', 'count': session['receive_count']})
	disconnect()


@socketio.on('my_ping')
def ping_pong():
	emit('my_pong')


@socketio.on('connect')
def test_connect():
	print ('connected')
	global thread
	with thread_lock:
		if thread is None:
			thread = socketio.start_background_task(target=background_thread)
	emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('add_trigger')
def add_trigger(msg):
	global posx, posy
	types = {
		'interval':  {
			'top': posx,
			'left': posy,
				'properties': {
				'title': 'Fixed Interval',
				'class': 'trigger-interval',
				'inputs': {},
				'outputs': {
					'out1': {'label': 'After' }
				}
			}
		},
		'random':  {
			'top': posx,
			'left': posy,
			'properties': {
				'title': 'Random Interval',
				'class': 'trigger-random',
				'inputs': {},
				'outputs': {
					'out1': {'label': 'Randomly' }
				}
			}
		},
		'input':  {
			'top': posx,
			'left': posy,
			'properties': {
				'title': 'Input Trigger',
				'class': 'trigger-input',
				'inputs': {},
				'outputs': {
					'out1': {'label': 'On HI' },
					'out2': {'label': 'On LO' }
				}
			}
		}
	}
	posx = posx + 20
	posy = posy + 20
	print ('emitting add_to_graph', posx, posy)
	emit('add_to_graph', {'data': types[msg['data']]})


@socketio.on('add_action')
def add_action(msg):
	global posx, posy
	types = {
		'output': {
			'top': posx,
			'left': posy,
			'properties': {
				'title': 'Set Output State',
				'class': 'action-output',
				'inputs': {
					'hi': { 'label': 'Set HI' },
					'low': { 'label': 'Set LOW' }
				},
				'outputs': {
					'after': { 'label': 'After Set' }
				}
			}
		},
		'toggle': {
			'top': posx,
			'left': posy,
			'properties': {
				'title': 'Toggle Output State',
				'class': 'action-toggle',
				'inputs': {
					'in': { 'label': 'In' }
				},
				'outputs': {
					'after': { 'label': 'After Toggle' }
				}
			}
		},
		'sound': {
			'top': posx,
			'left': posy,
				'properties': {
				'title': 'Play Sound',
				'class': 'action-sound',
				'inputs': {
					'in': { 'label': 'In' }
				},
				'outputs': {
					'after': { 'label': 'After Sound' }
				}
			}
		}
	}

	posx = posx + 20
	posy = posy + 20
	print ('emitting add_to_graph', posx, posy)
	emit('add_to_graph', {'data': types[msg['data']]})

def makeDict(array):
	obj = {}
	for item in array:
		obj[item['name']] = item['value']
	return obj


if __name__ == '__main__':
	socketio.run(app, debug=True)
