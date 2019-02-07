import discord
import argparse
import asyncio
import random
import urllib.request
import re
import os, io, sys
import importlib
import datetime, time
import botfiles.generic as generic

class BotObject:
    def __init__(self, botName, token):
        self.token = token
        self.name = botName
        sys.path.append("botfiles")
        package = importlib.__import__('botfiles', fromlist=[botName])
        self.module = getattr(package, botName)
        self.reloadModule()

    def reloadModule(self):
        self.module = importlib.reload(self.module)
        botClass = getattr(self.module, self.name.capitalize() + "Bot")
        self.bot = botClass("!")

    def stop(self):
        self.bot.stop()

def fetchToken(botName):
        dirname = os.path.dirname(__file__)
        secrets = open(os.path.join(dirname, "secrets.txt"), 'r')
        for line in secrets:
            parsed = line.split(":")
            if parsed[0] == botName:
                token = parsed[1].strip()
                secrets.close()
                return token

class MotherBot(generic.DiscordBot):
    botMap = {
        'mettaton': None,
        'philippe': None,
        'zenyatta': None
    }

    # Requires botMap to be mapped
    def restartChild(self,botName):
        if botName in self.botMap:
            botObj = self.botMap[botName]

            # self.killChild(botName)

            print("Restarting {}...".format(botName))

            botObj.reloadModule()
            botObj.bot.run(botObj.token)
            # threads[botName] = threading.Thread(target=botObj.bot.run, args=(botObj.token,), name="{}-thread".format(botName))
            # threads[botName].start()

            print("Restarted {}.".format(botName))

    def killChild(self, botName):
        botObj = self.botMap[botName]
        # if threads[botName] is not None:
        #     print("Shutting down {}...".format(botName))
        #     botObj.stop()
        #     threads[botName].join()
        #     threads[botName] = None
        #     print("Shut down {}.".format(botName))

    def __init__(self, prefix="!"):
        super().__init__(prefix, "MOTHER STARTING UP", "MOTHER SHUTTING DOWN")

        #Start Children
        for botName in self.botMap.keys():
            self.botMap[botName] = BotObject(botName, fetchToken(botName + ".py"))
            self.restartChild(botName)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mother Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    mother = MotherBot()
    mother.run(args.token[0])
