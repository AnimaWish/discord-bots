import discord
import asyncio
import random
import re
from .generic import DiscordBot
from .simplevote import SimpleVoteBot
from .event import EventBot
import argparse
import importlib

class GyoshinBot(SimpleVoteBot):
    ###################
    #    Constants    #
    ###################

    ###################
    #     Helpers     #
    ###################

    ###################
    #    Commands     #
    ###################

    ###################
    #   Bot Methods   #
    ###################

    def getName(self):
        return "gyoshin"

    def __init__(self, prefix="!"):
        super().__init__(prefix, "It is nice to be meeting you, yes, yes.", "I take my leave, yes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gyoshin Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    gyoshin = GyoshinBot()
    gyoshin.run(args.token[0])
