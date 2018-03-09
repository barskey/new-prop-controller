TRIGGERS = {
	'interval': {
		'top': 20,
		'left': 20,
			'properties':
			{
				'title': 'Fixed Interval',
				'class': 'trigger-interval',
				'inputs': {},
				'outputs': {
					'out1': {'label': 'Every 5s' }
				}
			}
		},
	'random': {
		'top': 20,
		'left': 20,
		'properties': {
			'title': 'Random Interval',
			'class': 'trigger-random',
			'inputs': {},
			'outputs': {
				'out1': {'label': 'Randomly' }
			}
		}
	},
	'input': {
		'top': 20,
		'left': 20,
		'properties': {
			'title': 'Input Trigger',
			'class': 'trigger-input',
			'inputs': {},
			'outputs': {
				'out1': {'label': 'On HI' },
				'out2': {'label': 'On LO' }
			}
		}
	}
}

ACTIONS = {
	'output': {
		'top': 20,
		'left': 20,
		'properties': {
			'title': 'Output State',
			'class': 'action-output',
			'inputs': {
				'hi': { 'label': 'Set HI' },
				'low': { 'label': 'Set LOW' },
				'toggle': { 'label': 'Toggle' }
			},
			'outputs': {
				'after': { 'label': 'Then' }
			}
		}
	},
	'sound': {
		'top': 20,
		'left': 20,
			'properties': {
			'title': 'Play Sound',
			'class': 'action-sound',
			'inputs': {
				'in': { 'label': 'In' }
			},
			'outputs': {
				'after': { 'label': 'Then' }
			}
		}
	}
}

CONTROLLER = {
	'input': 'HI',
	'outA': 'LO',
	'outB': 'LO',
	'outC': 'LO',
	'outD': 'LO'
}
