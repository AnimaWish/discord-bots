class TesterBot:
	TEST_CHANNEL_ID = "X"
	testchannel = None

	ZENYATTA_ID = "X"
	METTATON_ID = "Y"
	PHILIPPE_ID = "Z"

	idToName = {
		ZENYATTA_ID: "zenyatta",
		METTATON_ID: "mettaton",
		PHILIPPE_ID: "philippe",
	}

	responses = {}
	results = {}

	testmap = {
		"test1": [
			ZENYATTA_ID,
			METTATON_ID,
			PHILIPPE_ID,
		],
	}

	###################
    #      Tests      #
    ###################

	def test1(self):
		self.testchannel.send("!help")
		expectedResult = "/.+/"
		return expectedResult


	###################
	#    Execution     #
	###################

	def executeTests(self):
		for testName in testmap.keys():
			textExecTimestamp = time.now()

			results[testName] = {}

			expectedResult = testName.execute()
			sleep(1)

			# TODO this pattern sucks, the tests should handle everything on their own
			if expectedResult == False:
				# expect that *nothing* was said
				for botID in testmap[testName]:
					if responses[botID]:
						results[testName][botID] = False
					else:
						results[testName][botID] = True
			else: 
				for botID in testmap[testName]:
					# TODO regex match
					if responses[botID].content == expectedResult:
						results[testName][botID] = True
					else: 
						results[testName][botID] = False

			self.responses = {}


	def printResults(self):
		message = ""
		for testName in results.keys():
			for botID in results[testName].keys():
				if results[testName][botID] == False:
					message += idToName[botID] + "failed [" + testName + "]\n"

		self.testchannel.send(message)


	async def on_ready(self):
		for guild in self.client.guilds:
			testchannel = guild.get_channel(TEST_CHANNEL_ID)
			if testchannel != None:
				self.testchannel = testchannel
				break

		if self.testchannel == None:
			print("Could not find testing channel")

	async def on_message(self, message):
		if message.channel.id == TEST_CHANNEL_ID:
			self.responses[message.author.id] = message

	def __init__(self):
		print(asdf)
		executeTests()
		printResults()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tester Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    tester = TesterBot()
    tester.run(args.token[0])
