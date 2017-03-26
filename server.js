var app = require('express')();
var server = require('http').Server(app);
server.listen(80);

app.get('/', function (req, res) {
  res.sendfile('/index.html');
});
console.log('Express server started on port %s', server.address().port);