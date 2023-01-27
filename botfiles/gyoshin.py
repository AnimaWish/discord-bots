import discord
from .botmodules import SimpleVoteBot
import argparse

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

    def __init__(self, prefix="!", *, intents, **options):
        super().__init__(prefix, "It is nice to be meeting you, yes, yes.", "I take my leave, yes.", intents=intents, options=options)
