$( function() {
  $( '#dashboardMenu' ).addClass( 'active' );

  $( '#triggerMenu' ).collapse( 'show' );
  $( '#actionMenu' ).collapse( 'show' );

  //var Particle = require('particle-api-js');
  var particle = new Particle();
  var token;

  //------------------------- Functions ----------------------------------//
  var $dashboard = $( '#dashboard' );
  var $container = $dashboard.parent();

  var cx = $dashboard.width() / 2;
  var cy = $dashboard.height() / 2;

  // Panzoom initialization...
  $dashboard.panzoom();
  // Set defaults...
  $dashboard.panzoom('option', {
    increment: 0.1,
    minScale: 0.5,
    maxScale: 2,
    $reset: $( '#resetZoom' ),
    onReset: function()
    {
      $dashboard.flowchart( 'setPositionRatio', 1 );
    }
  });
  // Centering panzoom
  $dashboard.panzoom('pan', -15, 0);

  // Panzoom zoom handling...
  var possibleZooms = [0.5, 0.75, 1, 2, 3];
  var currentZoom = 2;
  $container.on('mousewheel.focal', function( e ) {
      e.preventDefault();
      var delta = (e.delta || e.originalEvent.wheelDelta) || e.originalEvent.detail;
      var zoomOut = delta ? delta < 0 : e.originalEvent.deltaY > 0;
      //currentZoom = Math.max(0, Math.min(possibleZooms.length - 1, (currentZoom + (zoomOut * 2 - 1))));
      $dashboard.panzoom('zoom', zoomOut, {
        animate: false,
        focal: e
      });
      var zoom = parseFloat( $dashboard.panzoom( 'getMatrix' )[0] );
      $dashboard.flowchart( 'setPositionRatio', zoom );
  });

  $dashboard.flowchart({
    data: {operators: {}, links: {}},
    multipleLinksOnInput: true,
    multipleLinksOnOutput: true,
    onAfterChange: function( type ) {
      var graphData = $dashboard.flowchart( 'getData' );
      socket.emit( 'save_graph', { data: graphData } );
      $( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-warning').text( 'Send Data');
      return true;
    },
    onOperatorSelect: function ( opid ) {
        socket.emit( 'get_op_params', { opid: opid } );
        return true;
    },
    onOperatorUnselect: function () {
      hideProperties();
      return true;
    },
    onOperatorDelete: function ( opid ) {
      socket.emit( 'delete_op_params', { opid: opid } );
      return true;
    },
    onLinkSelect: function ( opid ) {
      hideProperties();
      $( '#deleteSelectedLink' ).removeClass( 'd-none');
      $( '.edit-link' ).removeClass( 'd-none' );
      return true;
    },
    onLinkUnselect: function () {
      hideProperties();
      return true;
    }
  });

  $dashboard.flowchart('setPositionRatio', 1);

  function logResponse( response, style ) {
    $( '#log' ).prepend(
      $( '<li>' ).text( response ).addClass( 'list-group-item bg-light text-' + style )
    );
    $( '#log li:last-child').remove();
  };

  function hideProperties() {
    $( '#saveSelectedOp, #deleteSelectedOp, #deleteSelectedLink' ).addClass( 'd-none' );
    $( '.edit-timer, .edit-input, .edit-interval, .edit-random, .edit-output, .edit-title, .edit-link' ).addClass( 'd-none' );
  };

  function publish_event( name, data, partnum, total ) {
    var publishEventSendGraph = particle.publishEvent(
      {name: name, data: data, auth: token, isPrivate: true}
    );
    publishEventSendGraph.then(
      function( data ) {
        if ( data.body.ok ) {
          $( '#sendProgress' ).text(partnum + ' of ' + total).css('width', (partnum / total) * 100 + '%');
          console.log( name + ' published successfully.' );
          logResponse( name + ' published successfully.', 'success' );
        }
      },
      function( err ) {
        console.log( name + strPart + ' failed.' + err );
        logResponse( name + strPart + ' failed.', 'danger' );
      }
    );
  }

  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.
  namespace = '';
  // Connect to the Socket.IO server.
  // The connection URL has the following format:
  //	   http[s]://<domain>:<port>[/<namespace>]
  var socket = io.connect( location.protocol + '//' + document.domain + ':' + location.port + namespace );
  // Event handler for new connections.
  // The callback function is invoked when a connection with the
  // server is established.
  socket.on( 'connect', function() {
    socket.emit( 'show_graph' );
    console.log ( 'dashboard.js connected via socketio.' );
  });

  socket.on('get_token',  function(msg) {
    //3fc770faa4f820dd5503b18ae3bf9262be8430ba
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

  socket.on( 'create_graph', function(msg) {
    $dashboard.flowchart('setData', msg.data);
  });

  socket.on( 'send_graph', function(msg) {
  	if ( token ) {
      var counter = 0;
      var i = 0;
      // send publish events in chunks 250 characters or less
      var tot_parts = parseInt(msg.data.length / 250);
      $( '#modalButton' ).attr('disabled', true);
      while( counter < msg.data.length ) {
        var part = msg.data.substring( counter, counter + 250 );
        var t = i * 1500;
        var name = 'Graph/' + i.toString();
        setTimeout ( publish_event, t, name, part, i, tot_parts ); // delay them by 1 second to prevent them from caching together
        counter += 250;
        i++;
      }
      setTimeout ( function () {
        $( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-success').text( 'Sent' );
        $( '#modalButton' ).removeAttr('disabled').text( 'Done' );
      }, i * 1500 );
    } else {
      console.log( 'No valid token.' );
      logResponse( 'No valid token.', 'warning' );
    }
  });

  socket.on( 'show_params', function( msg ) {
    hideProperties();
	  $( '.edit-title, .edit-' + msg.params.type ).removeClass( 'd-none' );
		$( '#deleteSelectedOp' ).removeClass( 'd-none');
		$( '#op-type' ).val( msg.params.type );
    $( '#op-hexid' ).val(msg.params.hexid );
	  $( '#title' ).val( msg.params.title );
	  $( '#' + msg.params.type + '-param1' ).val( msg.params.param1 );
	  $( '#' + msg.params.type + '-param2' ).val( msg.params.param2 );
  });

  socket.on( 'log_response', function( msg ) {
    logResponse( msg.response, msg.style );
  });

  socket.on( 'add_to_graph', function( msg ) {
    $dashboard.flowchart( 'createOperator', msg.opid, msg.data );
    $dashboard.flowchart( 'selectOperator', msg.opid );
  });

  //------------------------- Click Handlers ----------------------------------//
  $( 'a.add-operator' ).click( function() {
    var type = $( this ).attr( 'data-type' );
    var hexid = $( this ).attr( 'data-hexid' );
    var port = '';
    if ( type == 'output' )
    {
      port = $( this ).attr( 'data-port' );
    }
    socket.emit( 'add_op', {type: type, hexid: hexid, port: port} );
  });

	$( 'input[type="text"]' ).change( function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		var type = $( '#op-type' ).val();
    var hexid = $( '#op-hexid' ).val();
		var optitle = $( '#title' ).val();
		var p1 = $( '#' + type + '-param1' ).val();
		var p2 = $( '#' + type + '-param2' ).val();
		$dashboard.flowchart( 'setOperatorTitle', opid, optitle );
		socket.emit( 'update_parameters', {opid: opid, hexid: hexid, title: optitle, param1: p1, param2: p2, type: type} );
	});

	$( '#deleteSelectedOp' ).click( function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		if (opid != null) {
			socket.emit( 'delete_op_params', { opid: opid });
			$dashboard.flowchart( 'deleteOperator', opid );
		}
	});

	$( '#deleteSelectedLink' ).click( function() {
		var opid = $dashboard.flowchart( 'getSelectedLinkId' );
		if (opid != null) {
			$dashboard.flowchart( 'deleteLink', opid );
		}
	});

	$( '#sendGraph' ).click( function() {
		socket.emit('parse_graph');
	});

  $( '#clearGraph' ).click( function() {
     graphData = {
   	  operators: {},
   	  links: {}
     };
     $dashboard.flowchart( 'setData', graphData );
     socket.emit( 'save_graph', { data: graphData } );
     socket.emit( 'clear_data', { data: graphData } );
     $( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-secondary').text( 'Up-to-Date');
     $( '#clear' ).modal( 'hide' );
  });

  $( '#clearLinks' ).click( function() {
    var graphData = $dashboard.flowchart( 'getData' );
    for ( var link in graphData['links'] ) {
      console.log( link );
      $dashboard.flowchart( 'deleteLink', link );
    }
    $( '#clear' ).modal( 'hide' );
  });
});
