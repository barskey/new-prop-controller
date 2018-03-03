$(document).ready(function() {
	var data = {
		operatorTypes: {
			trigger: {
				title: 'Trigger',
				inputs: {},
				outputs: {
					label: 'Trigger'
				},
			},
			action: {
				title: 'Action',
				inputs: {
					in1: {
						label: 'In'
					}
				},
				outputs: {
					out1: {
						label: 'After'
					}
				}
			}
		}
	};
	
	$('#dashboard').flowchart({
		data: data,
		multipleLinksOnInput: true,
		multipleLinksOnOutput: true
	});
});