TRIGGERS = {
	'timer': {
		'properties':
		{
			'title': 'One-Shot Timer',
			'class': 'trigger-timer',
			'inputs': {
				's': {'label': 'Start'}
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
				'h': {'label': 'On HI'},
				'l': {'label': 'On LO'}
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
				'H': {'label': 'Set HI'},
				'L': {'label': 'Set LOW'},
				'T': {'label': 'Toggle'}
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
				'P': {'label': 'Play'}
			},
			'outputs': {
				'after': {'label': 'Then'}
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
