import discord
import asyncio
import random
import urllib.request
import re
import os
from generic import DiscordBot, BotCommand
import argparse

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

    ###################
    #    Commands     #
    ###################

    def getHelp(self, message, params):
        return """
*Here comes a special bot! Here comes a special bot! Here comes a special bot!*

 - Type `!random` to get a random comic! Wow!    
 - Type `!prompt` to get a random discussion prompt! Hot dang!
 - Type `!search [search term]` to search comic dialogue! Holy smokes!
 - Type `!roll XdY` to roll X Y-sided dice!
 - Type `!choose a,list,of,things` to randomly select something from the list!

Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

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

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, token, prefix="!"):
        super().__init__(token, prefix)
        self.commandMap = {
            'help':   BotCommand(self.getHelp,        lambda x: True),
            'echo':   BotCommand(self.echo,           lambda x: True),
            'roll':   BotCommand(self.getDieRoll,     lambda x: True),
            'choose': BotCommand(self.chooseRand,     lambda x: True),
            'random': BotCommand(self.getRandomStrip, lambda x: True),
            'prompt': BotCommand(self.getPrompt,      lambda x: True),
            'search': BotCommand(self.searchStrips,   lambda x: True),
        }

    async def on_message(self, message):
        indexLinkMatch = re.search(PhilippeBot.INDEX_LINK_PATTERN, message.content)

        if indexLinkMatch:
            indexLink = 'http://' + message.content[indexLinkMatch.start():indexLinkMatch.end()]
            comicLink = indexLink.replace('index', 'comic')
            contents = urllib.request.urlopen(indexLink).read().decode("utf-8")
            titleText = PhilippeBot.parseTitle(contents)
            await self.client.send_message(message.channel, PhilippeBot.linkWithTitle(comicLink, titleText))

        await super().on_message(message)

if __name__ == "__main__":
    print("Here comes a special bot! Here comes a special bot! Here comes a special bot!")
    parser = argparse.ArgumentParser(description='Philippe Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    philippe = PhilippeBot(args.token[0])
    philippe.run()
