import discord
import asyncio
import urllib.request
import re
import random

client = discord.Client()

prompts = [
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

characters = [
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

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    linkPattern = 'achewood\.com\/index\.php\?date=\d+';
    
    indexLinkMatch = re.search(linkPattern, message.content)

    if message.content.startswith('!help'):
        await client.send_message(message.channel, getHelp())

    elif indexLinkMatch:
        indexLink = 'http://' + message.content[indexLinkMatch.start():indexLinkMatch.end()]
        comicLink = indexLink.replace('index', 'comic')
        contents = urllib.request.urlopen(indexLink).read().decode("utf-8")
        titleText = parseTitle(contents)

        await client.send_message(message.channel, linkWithTitle(comicLink, titleText))

    elif message.content.startswith('!random'):
        contents = urllib.request.urlopen('http://www.ohnorobot.com/random.pl?comic=636').read().decode("utf-8")
        await client.send_message(message.channel, getComicAndTitleFromPage(contents))

    elif message.content.startswith('!prompt'):
        await client.send_message(message.channel, getPrompt())  

    elif message.content.startswith('!search'):
        searchTerm = message.content[(len("!search") + 1):]

        linkSearchTerm = re.sub(' ', '+', searchTerm)

        if len(searchTerm) == 0:
            await client.send_message(message.channel, "I need a search term! e.g. `!search dirtiest dudes in town`")
            return
        
        searchResultsLink = "http://www.ohnorobot.com/index.php?comic=636&s={}&search=Find".format(linkSearchTerm)
        luckyLink = "http://www.ohnorobot.com/index.php?s={}&lucky=Let+the+Robot+Decide%21&comic=636".format(linkSearchTerm)

        contents = urllib.request.urlopen(luckyLink).read().decode("utf-8")
        bestGuess = getComicAndTitleFromPage(contents)

        result = "No results found!"
        if bestGuess:
            result = "Search Results: " + searchResultsLink;
            
        await client.send_message(message.channel, result)

        if bestGuess:
            await client.send_message(message.channel, bestGuess)



def parseTitle(contents):
    pattern = "/comic\.php\?date=\d+\" title=.*\""
    strings = re.findall(pattern, contents)
    if len(strings) > 0:
        titleText = strings[0][strings[0].index("title=") + len("title="):]
        if titleText == '""':
            titleText = "*(no alt text to display)*"

        return titleText

    return '*(alt text not found)*'

def linkWithTitle(link, title):
    if len(title) > 0:
        return link + "\n" + title

    return link

def getPrompt():
    prompt = random.choice(prompts)
    prompt = re.sub('\[CHARACTER\]', random.choice(characters), prompt)
    return prompt

def getHelp():
    return """
*Here comes a special bot! Here comes a special bot! Here comes a special bot!*

 - Type `!random` to get a random comic! Wow!    
 - Type `!prompt` to get a random discussion prompt! Hot dang!
 - Type `!search [search term]` to search comic dialogue! Holy smokes!

Hit up Wish#6215 for feature requests/bugs!
"""

def getComicAndTitleFromPage(contents):
    pattern = "/comic\.php\?date=\d+"
    strings = re.findall(pattern, contents)
    titleText = parseTitle(contents)
    if len(strings) > 0:
        comicLink = "http://achewood.com" + strings[0]
        return linkWithTitle(comicLink, titleText)
    else:
        return False

def fetchToken():
    secrets = open("secrets.txt", 'r')
    for line in secrets:
        parsed = line.split(":")
        if parsed[0] == __file__:
            return parsed[1]

client.run(fetchToken())