$( function() {
  console.log('hello');
  var Particle = require('particle-api-js');
  var particle = new Particle();
  var token;

  particle.login({username: 'barskey@gmail.com', password: 'CarlyAnn1102'}).then(
    function(data) {
      token = data.body.access_token;
    },
    function (err) {
      console.log('Could not log in.', err);
    }
  );

  //3fc770faa4f820dd5503b18ae3bf9262be8430ba

});
