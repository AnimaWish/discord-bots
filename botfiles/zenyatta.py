import discord
import asyncio
import random
import re
from .generic import DiscordBot
from .vote import VoteBot
from .event import EventBot
import argparse
import importlib

class ZenyattaBot(EventBot, VoteBot):
    ###################
    #    Constants    #
    ###################

    OVERWATACH_SERVER_ID = 199402098754846729

    GENTLEMEN_ROLE_ID = 432092120007049236
    ROBOTS_ROLE_ID = 433376740312875049

    EVENTS_CHANNEL_ID = 542851422333567007
    EVENT_PLANNING_CATEGORY_ID = 542857613524598804

    ###################
    #     Helpers     #
    ###################

    def memberIsGentleman(self, author):
        return ZenyattaBot.memberHasRole(author, ZenyattaBot.GENTLEMEN_ROLE_ID)

    def mentionGents(self, text):
        return '<@&{}>'.format(ZenyattaBot.GENTLEMEN_ROLE_ID) + ' ' + text

    ###################
    #    Commands     #
    ###################

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!"):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Zenyatta Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    zenyatta = ZenyattaBot()
    zenyatta.run(args.token[0])
