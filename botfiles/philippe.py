import discord
import asyncio
import random
import urllib.request
import re
import os
from generic import DiscordBot, BotCommand
import argparse
from datetime import datetime

class PhilippeBot(DiscordBot):
    ###################
    #    Constants    #
    ###################

    PROMPTS = [
        'What did you like best about this section?',
        'What did you like least about this section?',
        'What surprised you about this section?',
        'What did [CHARACTER] get up to in this section?',
        'How did this section affect your opinion about [CHARACTER]?',
        'How did this section affect your opinion about [CHARACTER]?',
        'Which comic in this section was your favorite?',
        'What new characters were introduced in this section?',
        'Who were the major players in this section?',
        'What major events happened in this section?'
    ]

    CHARACTERS = [
        'Ray',
        'Roast Beef',
        'Pat',
        'Téodor',
        'Philippe',
        'Mr. Bear',
        'Lyle',
        'Molly',
        'Chris',
        'Nice Pete',
        'Little Nephew',
        'Emeril'
    ]

    INDEX_LINK_PATTERN = 'achewood\.com\/index\.php\?date=\d+'
    SEARCH_URL = "http://www.ohnorobot.com/index.php?comic=636&s={}&search=Find"
    LUCKY_URL  = "http://www.ohnorobot.com/index.php?s={}&lucky=Let+the+Robot+Decide%21&comic=636"

    LOGFILE = "data/philippe/progress.txt"

    ###################
    #     Helpers     #
    ###################

    @staticmethod
    def parseTitle(contents):
        pattern = "/comic\.php\?date=\d+\" title=.*\""
        strings = re.findall(pattern, contents)
        if len(strings) > 0:
            titleText = strings[0][strings[0].index("title=") + len("title="):]
            if titleText == '""':
                titleText = "*(no alt text to display)*"

            return titleText

        return '*(alt text not found)*'

    @staticmethod
    def linkWithTitle(link, title):
        if len(title) > 0:
            return link + "\n" + title

        return link

    @staticmethod
    def getComicAndTitleFromPage(contents):
        pattern = "/comic\.php\?date=\d+"
        strings = re.findall(pattern, contents)
        titleText = PhilippeBot.parseTitle(contents)
        if len(strings) > 0:
            comicLink = "http://achewood.com" + strings[0]
            return PhilippeBot.linkWithTitle(comicLink, titleText)
        else:
            return False

    @staticmethod
    def indexMatch(input):
        indexLinkMatch = re.search(PhilippeBot.INDEX_LINK_PATTERN, input)

        if indexLinkMatch:
            indexLink = 'http://' + input[indexLinkMatch.start():indexLinkMatch.end()]
            comicLink = indexLink.replace('index', 'comic')
            contents = urllib.request.urlopen(indexLink).read().decode("utf-8")
            titleText = PhilippeBot.parseTitle(contents)
            return PhilippeBot.linkWithTitle(comicLink, titleText)

        return None

    def writeLogs(self):
        progFile = open(self.LOGFILE, "w")
        for key, value in self.progressLogs.items():
            progFile.write("{}~~{}".format(key, datetime.strftime(value, "%m%d%Y")))

        progFile.close()

    def readLogs(self):
        try:
            progFile = open(self.LOGFILE, "r")
        except FileNotFoundError:
            print("ERROR: No progress logs imported!")
            return

        logPattern = "(\d+)~~(.+)"
        for line in progFile:
            match = re.search(logPattern, line)
            if match is not None:
                self.progressLogs[match.group(1)] = datetime.strptime(match.group(2), "%m%d%Y")
            else:
                print("Error reading log: {}".format(line))

        progFile.close()

    ###################
    #    Commands     #
    ###################
    def getRandomStrip(self, message, params):
        contents = urllib.request.urlopen('http://www.ohnorobot.com/random.pl?comic=636').read().decode("utf-8")
        return PhilippeBot.getComicAndTitleFromPage(contents)

    def getPrompt(self, message, params):
        prompt = random.choice(PhilippeBot.PROMPTS)
        prompt = re.sub('\[CHARACTER\]', random.choice(PhilippeBot.CHARACTERS), prompt)
        return prompt

    def searchStrips(self, message, params):
        linkSearchTerm = re.sub(' ', '+', params)

        if len(params) == 0:
            return "I need a search term! e.g. `!search dirtiest dudes in town`"
        
        searchResultsLink = PhilippeBot.SEARCH_URL.format(linkSearchTerm)
        luckyLink         = PhilippeBot.LUCKY_URL.format(linkSearchTerm)

        luckyContents = urllib.request.urlopen(luckyLink).read().decode("utf-8")
        bestGuess = PhilippeBot.getComicAndTitleFromPage(luckyContents)

        result = "No results found!"
        if bestGuess:
            result = "**Search Results:** {}".format(searchResultsLink)

        if bestGuess:
            result += "\n\n**Best Guess:** {}".format(bestGuess)

        return result

    def logProgress(self, message, params):
        comicLink = PhilippeBot.indexMatch(params)
        dateText = ""
        isValid = True
        if comicLink is not None:
            rPattern = "(.*date=)(\d+)"
            match = re.search(rPattern, comicLink)
            if match is not None:
                dateText = match.group(2)
                dtime = datetime.strptime(dateText, "%m%d%Y")
        else:
            formats = [
                "%m-%d-%Y",
                "%m/%d/%Y",
                "%m/%d/%y",
                "%x",
                "%m-%d-%y",
                "%B %d, %Y",
                "%m%d%Y"
            ]

            dtime = ""
            for format in formats:
                isValid = True
                try:
                    dtime = datetime.strptime(params, format)
                except ValueError:
                    isValid = False

                if isValid:
                    break

        
        if isValid:
            print(dtime)
            self.progressLogs[message.author.id] = dtime
            self.writeLogs()
            return "Logged {}!".format(dtime.strftime("%B %d, %Y"))
        else:
            return "Couldn't parse date. Try pasting a comic link or using the format MM-DD-YYYY"

    async def getProgressLogs(self, message, params):
        result = ""
        longestName = 0
        names = {}
        for k in self.progressLogs:
            names[k] = await self.client.get_user_info(k)
            if len(names[k]) > longestName:
                longestName = len(names[k])

        for k,v in self.progressLogs.items():
            spaceBuffer = longestName + 1 + len(names[k])
            dateText = v.strftime("%b %d, %Y")
            line = "{}{}- {}\n".format(names[k], ' '*spaceBuffer, dateText)
            result += line

        return result

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!"):
        super().__init__(prefix, "Here comes a special bot! Here comes a special bot! Here comes a special bot!", "Bye bye!")

        self.addCommand('random', self.getRandomStrip,  lambda x: True, "Get a random comic")
        self.addCommand('prompt', self.getPrompt,       lambda x: True, "Get a random discussion prompt")
        self.addCommand('search', self.searchStrips,    lambda x: True, "Search comic dialogue", "[searchterms]")
        #self.addCommand('log',    self.logProgress,     lambda x: True, "Log your progress in the comic", "[comic link or date]")
        #self.addCommand('logs',   self.getProgressLogs, lambda x: True, "Print recorded progress logs")

        self.progressLogs = {}
        self.readLogs()

    async def on_message(self, message):
        comicLink = PhilippeBot.indexMatch(message.content)
        if comicLink is not None:
            await self.client.send_message(message.channel, comicLink)

        await super().on_message(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Philippe Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    philippe = PhilippeBot()
    philippe.run(args.token[0])
