$(document).ready(function() {
  $('#controllerMenu').addClass('active');
  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.
  namespace = '';
  // Connect to the Socket.IO server.
  // The connection URL has the following format:
  //	   http[s]://<domain>:<port>[/<namespace>]
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  // Event handler for new connections.
  // The callback function is invoked when a connection with the
  // server is established.
  socket.on('connect', function() {
    socket.emit('my_event', {data: 'I\'m connected!'});
  });
  // Event handler for server sent data.
  // The callback function is invoked whenever the server emits data
  // to the client. The data is then displayed in the "Received"
  // section of the page.
  socket.on('my_response', function(msg) {
    $('#log').text('Received #' + msg.count + ': ' + msg.data).html();
  });

  socket.on('controller_ping', function(msg) {
    console.log(msg.data);
    socket.emit('ping_received', {data: msg.data});
  });

  // Handlers for the different forms in the page.
  // These accept data from the user and send it to the server in a
  // variety of ways
  $('form#emit').submit(function(event) {
    socket.emit('my_event', {data: $('#emit_data').val()});
    return false;
  });

  $('form#broadcast').submit(function(event) {
    socket.emit('my_broadcast_event', {data: $('#broadcast_data').val()});
    return false;
  });

  $( '#addController' ).click( function() {
    socket.emit( 'sim_controller_connected' );
  });
  
  $( '#clearControllers' ).click( function() {
	socket.emit( 'clear_data', {data: 'all'} );
  });

  $( '#clearGraph' ).click( function() {
	  console.log('cleargraph');
	socket.emit( 'clear_data', {data: 'graph'} );
  });

  $( ':checkbox' ).change( function() {
    var id = $( this ).parents( '.card' ).attr( 'id' );
    var outport = $( this ).attr( 'data-port' );
    var state = $( this ).prop( 'checked' );
    socket.emit( 'update_controller', {cid: id, port: outport, val: state} );
  });
});
