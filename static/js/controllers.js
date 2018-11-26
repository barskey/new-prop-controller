$(document).ready(function() {
  $('#controllerMenu').addClass( 'active' );

  //------------------------- Functions ----------------------------------//
  function logResponse( response, style ) {
    $( '#log' ).prepend(
      $( '<li>' ).text( response ).addClass( 'list-group-item bg-light text-' + style )
    );
    $( '#log li:last-child').remove();
  };

  //var Particle = require('particle-api-js');
  var particle = new Particle();
  var token;

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
    console.log ( 'Contollers.js connected via socketio.' );
  });

  socket.on('get_token',  function( msg ) {
    particle.login( {username: msg.username, password: msg.pwd} ).then(
      function( data ) {
        token = data.body.access_token;
        console.log( 'Token received.' );
        logResponse( 'Token received.', 'success' );
      },
      function ( err ) {
        console.log( 'Could not log in.', err );
        logResponse( 'Could not log in to Particle.', 'danger' );
      }
    );
  });

  socket.on( 'send_defaults', function( msg ) {
    if (token) {
      // publish event to Partile cloud with default controller states
      var publishEventDefaults = particle.publishEvent( {name: 'defaults/' + msg.cid, data: msg.data, auth: token, private: 'true'} );
      publishEventDefaults.then(
        function( data ) {
          if ( data.body.ok ) {
            console.log( 'Defaults published successfully.' );
            logResponse( 'Defaults published successfully.', 'success' );
          }
        },
        function( err ) {
          console.log( 'Defaults publish failed.' + err );
          logResponse( 'Defaults publish failed.', 'danger' );
        }
      );
    } else {
      console.log( 'No valid token.' );
      logResponse( 'No valid token.', 'warning' );
    }
  });

  socket.on( 'log_response', function( msg ) {
    logResponse( msg.response, msg.style );
  });

  $( '#clearControllers' ).click( function() {
	   socket.emit( 'clear_data', {data: 'all'} );
  });

  $( '#clearGraph' ).click( function() {
	   console.log( 'cleargraph' );
	   socket.emit( 'clear_data', {data: 'graph'} );
  });

  $( ':checkbox' ).change( function() {
    console.log('checkbox changed');
    var id = $( this ).parents( 'tr' ).attr( 'id' );
    var outport = $( this ).attr( 'data-port' );
    var state = $( this ).prop( 'checked' );
    socket.emit( 'update_controller', {cid: id, key: outport, val: state} );
  });

  $( '.btn' ).click( function () {
    $( this ).parents( '.input-group' ).children( 'input' ).attr( 'readonly', false );
  });

  $( "input[name='cname']" ).change( function () {
    var id = $( this ).parents( 'tr' ).attr( 'id' );
    var name = $( this ).val();
    socket.emit( 'update_controller', {cid: id, key: 'name', val: name} );
    $( this ).attr( 'readonly', true );
  });
});
