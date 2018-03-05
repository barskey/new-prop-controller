$(document).ready(function() {
	var data = {};

	$('#dashboard').flowchart({
		data: data
	});
});

function addTrigger(trigger) {
	var newli = $('<li></li>').addClass('list-group-item');
	newli.text(trigger['triggerName']);
	newli.attr('id', 'my_id');
	$('#triggerList').append(newli);
}
