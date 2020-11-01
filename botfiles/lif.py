import discord
import asyncio
from .botmodules import TTRPGBot
import argparse

class LifBot(TTRPGBot):
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
        return "lif"

    def __init__(self, prefix="!"):
        super().__init__(prefix, "*pours a drink*", "*ouija marker goes limp*")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lif Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    liff = LiffBot()
    liff.run(args.token[0])
