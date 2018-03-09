$( document ).ready( function() {
  $( '#dashboardMenu' ).addClass( 'active' );

  $( '#triggerMenu' ).collapse( 'show' );
  $( '#actionMenu' ).collapse( 'show' );

  $( '#editTrigger' ).BootSideMenu({
  	side: 'right',
  	pushBody: false,
  	remember: false,
  	autoClose: true,
  	width: '280px',
  	duration: 300,
    closeOnClick: false
  });

  var data = {
	  operators: {},
	  links: {}
  };

  var $dashboard = $( '#dashboard' );

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
    socket.emit('connected');
  });

  socket.on('create_graph', function(msg) {
	  $dashboard.flowchart({
		data: msg.data,
		onAfterChange: function( type ) {
			var graphData = $dashboard.flowchart( 'getData' );
			socket.emit( 'save_graph', { data: graphData } );
		},
		onOperatorSelect: function ( opId ) {
		    socket.emit( 'get_op_params', { data: opId } );
			console.log (opId + ' selected');
			return true;
		}
	  });
  });
  // Event handler for server sent data.
  // The callback function is invoked whenever the server emits data
  // to the client. The data is then displayed in the "Received"
  // section of the page.
  socket.on('my_response', function(msg) {
    $('#log').prepend($('<div/>').text('Received #' + msg.count + ': ' + msg.data).html() + '<br>');
  });

  socket.on('add_to_graph', function(msg) {
    $( '#dashboard' ).flowchart( 'createOperator', msg.id, msg.data );
    $dashboard.flowchart( 'selectOperator', msg.id );
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
  $('form#addTrigger').submit(function(event) {
    socket.emit('add_trigger', {data: $('form#addTrigger').serializeArray()});
    return false;
  });
  $('form#addAction').submit(function(event) {
    socket.emit('add_action', {data: $('form#addAction').serializeArray()});
    return false;
  });

  //------------------------- Click Handlers ----------------------------------//
  $( 'a.add-trigger, a.add-action' ).click( function() {
    var type = $( this ).attr( 'data-type' );
    var cid = $( this ).attr( 'data-cid' );
    socket.emit('add_op', {type: type, cid: cid});
  });

  //------------------------- Select Change Handlers --------------------------//
  $( '#triggerType' ).change( function() {
    $( '#addTrigger' ).find( ".triggerInterval" ).addClass( "d-none" );
    $( '#addTrigger' ).find( ".triggerRandom" ).addClass( "d-none" );
    $( '#addTrigger' ).find( ".triggerInput" ).addClass( "d-none" );
    var type = $( this ).find( "option:selected" ).text();
    $( '#addTrigger' ).find( ".trigger" + type ).removeClass( "d-none" );
  });

  $( '#actionType' ).change( function() {
    $( '#addAction' ).find( ".actionOutput" ).addClass( "d-none" );
    $( '#addAction' ).find( ".actionSound" ).addClass( "d-none" );
    var type = $( this ).find( "option:selected" ).val();
    console.log(type);
    $( '#addAction' ).find( ".action" + type ).removeClass( "d-none" );
  });
});
