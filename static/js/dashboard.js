$( function() {
  $( '#dashboardMenu' ).addClass( 'active' );

  $( '#triggerMenu' ).collapse( 'show' );
  $( '#actionMenu' ).collapse( 'show' );

  var $sideMenu = $( '#editOperator' );
  $sideMenu.BootSideMenu({
  	side: 'right',
  	pushBody: false,
  	remember: false,
//  	autoClose: true,
  	width: '300px',
  	duration: 300,
    closeOnClick: false
  });

  var data = {
	  operators: {},
	  links: {}
  };

  //------------------------- Functions ----------------------------------//
  function logResponse( response, style ) {
    $( '#log' ).prepend(
      $( '<li>' ).text( response ).addClass( 'list-group-item bg-light text-' + style )
    );
    $( '#log li:last-child').remove();
  };

  function hideSideMenuProperties() {
    $( '#saveSelectedOp, #deleteSelectedOp, #deleteSelectedLink' ).addClass( 'd-none' );
    $( '.edit-timer, .edit-input, .edit-interval, .edit-random, .edit-output, .edit-title, edit-link' ).addClass( 'd-none' );
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
  var socket = io.connect( location.protocol + '//' + document.domain + ':' + location.port + namespace );
  // Event handler for new connections.
  // The callback function is invoked when a connection with the
  // server is established.
  socket.on( 'connect', function() {
    socket.emit( 'show_graph' );
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
	  $dashboard.flowchart({
			data: msg.data,
			multipleLinksOnInput: true,
			multipleLinksOnOutput: true,
			onAfterChange: function( type ) {
				var graphData = $dashboard.flowchart( 'getData' );
				socket.emit( 'save_graph', { data: graphData } );
				$( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-warning').text( 'Send Data');
        return true;
			},
			onOperatorSelect: function ( opId ) {
					socket.emit( 'get_op_params', { id: opId } );
					return true;
			},
			onOperatorUnselect: function () {
				hideSideMenuProperties();
				return true;
			},
			onOperatorDelete: function ( opId ) {
				socket.emit( 'delete_op_params', { id: opId } );
				return true;
			},
			onLinkSelect: function ( opId ) {
        hideSideMenuProperties();
				$( '.edit-link' ).removeClass( 'd-none' );
				$( '#deleteSelectedLink' ).removeClass( 'd-none');
        $sideMenu.BootSideMenu.open();
				return true;
			},
			onLinkUnselect: function () {
        hideSideMenuProperties();
				return true;
			}
	  });
  });

  socket.on( 'send_graph', function(msg) {
  	if (token) {
      var strPart;
      if (!msg.complete) {
        strPart = msg.part;
        var publishEventSendGraph = particle.publishEvent( {name: 'Graph/' + strPart, data: msg.data, auth: token, private: 'true'} );
        publishEventSendGraph.then(
          function( data ) {
            if ( data.body.ok ) {
              console.log( 'Graph/' + strPart + ' published successfully.' );
              logResponse( 'Graph/' + strPart + ' published successfully.', 'success' );
            }
          },
          function( err ) {
            console.log( 'Graph/' + strPart + ' failed.' + err );
            logResponse( 'Graph/' + strPart + ' failed.', 'danger' );
          }
        );
      } else {
        $( '#sendGraph' ).removeClass( 'btn-warning btn-success' ).addClass( 'btn-success').text( 'Sent' );
      }
    } else {
      console.log( 'No valid token.' );
      logResponse( 'No valid token.', 'warning' );
    }
  });

  socket.on( 'show_params', function( msg ) {
    hideSideMenuProperties();
	  $( '.edit-title, .edit-' + msg.params.type ).removeClass( 'd-none' );
		$( '#saveSelectedOp, #deleteSelectedOp' ).removeClass( 'd-none');
		$( '#op-type' ).val( msg.params.type );
	  $( '#title' ).val( msg.params.title );
	  $( '#' + msg.params.type + '-param1' ).val( msg.params.param1 );
	  $( '#' + msg.params.type + '-param2' ).val( msg.params.param2 );
    $sideMenu.BootSideMenu.open();
  });

  socket.on( 'log_response', function( msg ) {
    logResponse( msg.response, 'success' );
  });

  socket.on( 'add_to_graph', function( msg ) {
    $dashboard.flowchart( 'createOperator', msg.id, msg.data );
    $dashboard.flowchart( 'selectOperator', msg.id );
  });

  //------------------------- Click Handlers ----------------------------------//
  $( 'a.add-operator' ).click( function() {
    var type = $( this ).attr( 'data-type' );
    var cid = $( this ).attr( 'data-cid' );
    socket.emit( 'add_op', {type: type, cid: cid} );
  });

	$( '#saveSelectedOp' ).click ( function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		var type = $( '#op-type' ).val();
		var optitle = $( '#title' ).val();
		var p1 = $( '#' + type + '-param1' ).val();
		var p2 = $( '#' + type + '-param2' ).val();
		$dashboard.flowchart( 'setOperatorTitle', opid, optitle );
		socket.emit( 'update_parameters', {opid: opid, title: optitle, param1: p1, param2: p2, type: type} );
	});

	$( '#deleteSelectedOp' ).click ( function() {
		var opid = $dashboard.flowchart( 'getSelectedOperatorId' );
		if (opid) {
			socket.emit( 'delete_op_params', { id: opid });
			$dashboard.flowchart( 'deleteOperator', opid );
		}
	});

	$( '#deleteSelectedLink' ).click ( function() {
		var opid = $dashboard.flowchart( 'getSelectedLinkId' );
		if (opid) {
			$dashboard.flowchart( 'deleteLink', opid );
		}
	});

	$( '#sendGraph' ).click ( function() {
		socket.emit('parse_graph');
	});
});
