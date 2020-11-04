import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading
import datetime, time

from .generic import DiscordBot

class SimpleVoteBot(DiscordBot):
    EMOJI_SETS = {
        "letters": ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"],
        "mammals": ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐵","🐺","🐗","🐴",], 
        "fish": ["🐙","🦑","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🦈","🐊","🐚","🦐","🦞"], 
        "bugs": ["🐝","🐛","🦋","🐌","🐞","🦟","🦗","🦂",],
        "plants": ["🌵","🌲","🌴","🍁","🍄","💐","🌹","🌻","🌳"],
        "fruit": ["🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🍈","🍒","🍑","🥭","🍍","🥥","🥝",],
        "vegetables": ["🍅","🥑","🥦","🥒","🌶","🌽","🥕","🧅","🥔",],
        "junkfood": ["🥨","🧀","🥓","🥞","🧇","🍗","🌭","🍔","🍟","🍕","🥪","🌮","🍝","🎂","🍭","🍫","🍿","🍩","🍪",],
        "drinks": ["🍺","🥂","🍷","🥃","🍸","🍹",],
        "sports": ["⚽", "🏀","🏈","⚾","🎾","🏐","🏉","🥏","🎱","🏓","🏸","🏒","🏏",],
        "instruments": ["🎹","🥁","🎷","🎺","🎸","🪕","🎻","🎤",],
        "vehicles": ["🚗","🚕","🚌","🏎","🚓","🚑","🚒","🚛","🚜","🚲","🛵","🚂","✈️","🚀","🛸","🚁","🚤","⛵️",],
        "misc": ["🔫","🧲","💣","🔪","🚬","⚰️","🔮","🔬","💊","💉","🧬","🦠","🌡","🧸","🎁","💿","⏰","🧯","💎",], 
    }

    async def callVote(self, message, params):
        ballotPattern = "^([^\?]+\?)\s*(.+)$"

        ballotMatch = re.match(ballotPattern, params)

        if ballotMatch == None:
            await message.channel.send("I couldn't read your referendum. It should look like this: `!vote An Important Question? Choice A, Choice B, Choice C`. Remember the question mark and the commas, punctuation is important for robots!")
            return

        ballotText = ballotMatch.group(1)
        choices = ballotMatch.group(2).split(",")[:20]

        # Construct the emoji map
        # emojiMap = {} # emojiMap[choiceID] = emoji
        # emojiCode = 127462 # :regional_identifier_a:
        # for i, choice in enumerate(choices):
        #     emojiMap[i] = chr(emojiCode)
        #     emojiCode = emojiCode + 1

        validEmojiSets = []
        for key, emojiSet in SimpleVoteBot.EMOJI_SETS.items():
            if len(emojiSet) >= len(choices):
                validEmojiSets.append(key)

        emojiSetKey = random.choice(validEmojiSets)
        emojiMap = SimpleVoteBot.EMOJI_SETS[emojiSetKey]
        if emojiSetKey != "letters":
            random.shuffle(emojiMap)

        def constructBallotMessage(text, choices, emojiMap):
            ballotMessage = "__**Referendum:**__ {}\n\n__**Choices**__".format(text)
            for i, choice in enumerate(choices):
                ballotMessage = "{}\n{} {}".format(ballotMessage, emojiMap[i], choice.strip())

            ballotMessage = ballotMessage + "\n\n*Click an emoji below to vote! You can see how people voted by clicking \"Reactions\" in the menu on this message!*"

            return ballotMessage

        postedMessage = await message.channel.send(constructBallotMessage(ballotText, choices, emojiMap))

        # Add the ballot options as reactions. If we get a Forbidden error, that means that people added extra reactions before the bot could finish adding them.
        # In that case, we're going to adjust the ballot to use their reactions as options.
        injectedReaction = False
        for i, choice in enumerate(choices):
            try:
                await postedMessage.add_reaction(emojiMap[i])
            except discord.errors.Forbidden:
                injectedReaction = True
                break

        if injectedReaction:
            updatedPostedMessage = await message.channel.fetch_message(postedMessage.id)
            for i, reaction in enumerate(updatedPostedMessage.reactions):
                emojiMap[i] = reaction.emoji

            await postedMessage.edit(content=constructBallotMessage(ballotText, choices, emojiMap))

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.addCommand('vote', self.callVote, lambda x: True, "Call a vote", "Who is the best Star Trek captain? Kirk, Picard, Janeway")