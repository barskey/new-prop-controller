TRIGGERS = {
	'timer': {
		'properties':
		{
			'title': 'One-Shot Timer',
			'class': 'trigger-timer',
			'inputs': {
				'in1': {'label': 'Start'}
			},
			'outputs': {
				'out1': {'label': 'After Timer'}
			}
		}
	},
	'interval': {
		'properties':
		{
			'title': 'Fixed Interval',
			'class': 'trigger-interval',
			'inputs': {},
			'outputs': {
				'out1': {'label': 'On Interval'}
			}
		}
	},
	'random': {
		'properties': {
			'title': 'Random Interval',
			'class': 'trigger-random',
			'inputs': {},
			'outputs': {
				'out1': {'label': 'Randomly'}
		}
	}
},
	'input': {
		'properties': {
			'title': 'Input Trigger',
			'class': 'trigger-input',
			'inputs': {},
			'outputs': {
				'out1': {'label': 'On HI'},
				'out2': {'label': 'On LO'}
			}
		}
	}
}

ACTIONS = {
	'output': {
		'properties': {
			'title': 'Output State',
			'class': 'action-output',
			'inputs': {
				'hi': {'label': 'Set HI'},
				'low': {'label': 'Set LOW'},
				'toggle': {'label': 'Toggle'}
			},
			'outputs': {
				'after': {'label': 'Then'}
			}
		}
	},
	'sound': {
			'properties': {
			'title': 'Play Sound',
			'class': 'action-sound',
			'inputs': {
				'in1': {'label': 'Play'}
			},
			'outputs': {
				'out1': {'label': 'Then'}
			}
		}
	}
}

CONTROLLER = {
	'input': '1',
	'A': '0',
	'B': '0',
	'C': '0',
	'D': '0'
}
