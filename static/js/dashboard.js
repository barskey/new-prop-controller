$( function() {
  $( '#dashboardMenu' ).addClass( 'active' );

  $( '#triggerMenu' ).collapse( 'show' );
  $( '#actionMenu' ).collapse( 'show' );

  var $sideMenu = $( '#editOperator' );
  $sideMenu.BootSideMenu({
  	side: 'right',
  	pushBody: false,
  	remember: false,
  	autoClose: true,
  	width: '300px',
  	duration: 300,
    closeOnClick: false
  });

  var data = {
	  operators: {},
	  links: {}
  };

  function logResponse(response, style) {
    $('#log').prepend(
      $('<li>').text( response ).addClass( 'text-' + style )
    );
  };

  var $dashboard = $( '#dashboard' );

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
    socket.emit('show_graph');
  });

  socket.on('get_token',  function(msg) {
	//3fc770faa4f820dd5503b18ae3bf9262be8430ba
    particle.login({username: msg.username, password: msg.pwd}).then(
      function(data) {
        token = data.body.access_token;
        console.log('Logged in to Particle. Token received.');
      },
      function (err) {
        console.log('Could not log in.', err);
      }
    );
  });

  socket.on('create_graph', function(msg) {
	  $dashboard.flowchart({
			data: msg.data,
			multipleLinksOnInput: true,
			multipleLinksOnOutput: true,
			onAfterChange: function( type ) {
				var graphData = $dashboard.flowchart( 'getData' );
				socket.emit('save_graph', { data: graphData } );
				$( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-warning').text( 'Send Data');
			},
			onOperatorSelect: function ( opId ) {
					socket.emit( 'get_op_params', { id: opId } );
					return true;
			},
			onOperatorUnselect: function () {
				$sideMenu.BootSideMenu.close();
				return true;
			},
			onOperatorDelete: function ( opId ) {
				socket.emit( 'delete_op_params', { id: opId } );
				return true;
			},
			onLinkSelect: function ( opId ) {
				$( '#deleteSelectedOp' ).addClass( 'd-none' );
				$( '.edit-timer, .edit-input, .edit-interval, .edit-random, .edit-output, .edit-title' ).addClass( 'd-none' );
				$( '.edit-link' ).removeClass( 'd-none' );
				$( '#deleteSelectedLink' ).removeClass( 'd-none');
				$sideMenu.BootSideMenu.open();
				return true;
			},
			onLinkUnselect: function () {
				$sideMenu.BootSideMenu.close();
				return true;
			}
	  });
  });

  socket.on('send_graph', function(msg) {
	if (token) {
		if (!msg.complete) {
			var publishEventSendGraph = particle.publishEvent({name: 'Graph/' + msg.part, data: msg.data, auth: token});
			publishEventSendGraph.then(
			  function(data) {
				if (data.body.ok) {
					console.log('Event published successfully.', data.body);
          logResponse('Event published successfully.', 'success');
				}
			  },
			  function(err) {
				  console.log('Failed to publish event:' + err);
          logResponse('Failed to publish event.', 'danger');
			  }
			);
		} else {
			console.log('Message complete.' + msg.part + ' messages published.');
      logResponse('Message publish complete.', 'success');
			$( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-success').text( 'Sent' );
		}
	} else {
		console.log('Tried to publish graph but no valid token.');
    logResponse('Tried to publish graph but no valid token.', 'warning');
	}
  });

  socket.on( 'show_params', function( msg ) {
	  console.log(msg);
		$( '#deleteSelectedLink' ).addClass( 'd-none' );
	  $( '.edit-timer, .edit-input, .edit-interval, .edit-random, .edit-output, .edit-link' ).addClass( 'd-none' );
	  $( '.edit-title, .edit-' + msg.params.type ).removeClass( 'd-none' );
		$( '#deleteSelectedOp' ).removeClass( 'd-none');
		$( '#op-type' ).val( msg.params.type );
	  $( '#title' ).val( msg.params.title );
	  $( '#' + msg.params.type + '-param1' ).val( msg.params.param1 );
	  $( '#' + msg.params.type + '-param2' ).val( msg.params.param2 );
	  $sideMenu.BootSideMenu.open();
  });

  socket.on('log_response', function(msg) {
    logResponse(msg.response, 'success');
  });

  socket.on('add_to_graph', function(msg) {
    $dashboard.flowchart( 'createOperator', msg.id, msg.data );
    $dashboard.flowchart( 'selectOperator', msg.id );
  });

  //------------------------- Click Handlers ----------------------------------//
  $( 'a.add-operator' ).click( function() {
    var type = $( this ).attr( 'data-type' );
    var cid = $( this ).attr( 'data-cid' );
    socket.emit('add_op', {type: type, cid: cid});
  });

  $( '#cancelEdit' ).click( function() {
	  $dashboard.flowchart( 'unselectOperator' );
  });

	$( '#saveSelectedOp' ).click ( function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		var type = $( '#op-type' ).val();
		var optitle = $( '#title' ).val();
		var p1 = $( '#' + type + '-param1' ).val();
		var p2 = $( '#' + type + '-param2' ).val();
		$dashboard.flowchart( 'setOperatorTitle', opid, optitle );
		socket.emit( 'update_parameters', {opid: opid, title: optitle, param1: p1, param2: p2, type: type});
	});

	$( '#deleteSelectedOp' ).click (function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		if (opid) {
			socket.emit( 'delete_op_params', { id: opid });
			$dashboard.flowchart( 'deleteOperator', opid );
		}
	});

	$( '#deleteSelectedLink' ).click (function() {
		var opid = $dashboard.flowchart( 'getSelectedLinkId' );
		if (opid) {
			$dashboard.flowchart( 'deleteLink', opid );
		}
	});

	$( '#sendGraph' ).click ( function() {
		socket.emit('parse_graph');
	});
});
