from threading import Lock
from flask import Flask, render_template, session, request, url_for
from flask_socketio import SocketIO, emit, disconnect

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

op = {
	'title': 'Title',
	'top': 20,
	'left': 20,
}

def background_thread():
	"""Example of how to send server generated events to clients."""
	count = 0
	while True:
		socketio.sleep(10)
		count += 1
		socketio.emit('my_response', {'data': 'Server generated event', 'count': count})


@app.route('/')
def index():
	return render_template('index.html', async_mode=socketio.async_mode)


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
	global thread
	with thread_lock:
		if thread is None:
			thread = socketio.start_background_task(target=background_thread)
	emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
	print('Client disconnected', request.sid)

@socketio.on('add_node')
def add_node(message):
	global op
	op_to_add = op
	op_to_add['type'] = message['data']
	op_to_add['title'] = op['title'] + '1'
	emit('add_to_graph',
		{'data': op_to_add})

if __name__ == '__main__':
	socketio.run(app, debug=True)