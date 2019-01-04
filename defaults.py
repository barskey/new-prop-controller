TRIGGERS = {
	'timer': {
		'properties':
		{
			'title': 'Wait for Seconds',
			'class': 'trigger-timer',
			'inputs': {
				's': {'label': 'Start'}
			},
			'outputs': {
				'out1': {'label': 'After Wait'}
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
				'h': {'label': 'When ON'},
				'l': {'label': 'When OFF'}
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
				'H': {'label': 'Turn ON'},
				'L': {'label': 'Turn OFF'},
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
	'name': 'Controller',
	'cid': '',
	'type': '',
	'input': '1',
	'A': '0',
	'B': '0',
	'C': '0',
	'D': '0'
}
