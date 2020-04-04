import discord
import asyncio
import random
import re
import os
from .ttrpg import TTRPGBot
import argparse
import importlib

class LiffBot(TTRPGBot):
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
        return "liff"

    def __init__(self, prefix="!"):
        super().__init__(prefix, "*pours a drink*", "*ouija marker goes limp*")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Liff Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    liff = LiffBot()
    liff.run(args.token[0])
