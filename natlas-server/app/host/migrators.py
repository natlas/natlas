def determine_data_version(hostdata):
	if 'agent_version' in hostdata:
		# Do (bad) math on version here to determine if we need to fall "up" to 0.6.4
		version = hostdata['agent_version']
		verlist = version.split('.')
		for idx, item in enumerate(verlist):
			verlist[idx] = int(item)

		if verlist[1] < 6 or (verlist[1] == 6 and verlist[2] < 4):
			version = '0.6.4'
	else:
		# Fall "up" to 0.6.4 which is the last release before we introduced versioned host templates
		version = '0.6.4'

	return version
