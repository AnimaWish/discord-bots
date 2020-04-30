# import discord
import asyncio
import os
#import botfiles.generic
import botfiles

def fetchToken(botName):
        dirname = os.path.dirname(__file__)
        secrets = open(os.path.join(dirname, "secrets.txt"), 'r')
        for line in secrets:
            parsed = line.split(":")
            if parsed[0] == botName:
                token = parsed[1].strip()
                secrets.close()
                return token


if __name__ == "__main__":
    bots = {
        "philippe": botfiles.PhilippeBot(),
        "mettaton": botfiles.MettatonBot(),
        "zenyatta": botfiles.ZenyattaBot(),
        "lif":      botfiles.LifBot(),
        "gyoshin":  botfiles.GyoshinBot(),
    }

    loop = asyncio.get_event_loop()
    for botName in bots.keys():
        loop.create_task(bots[botName].client.start(fetchToken(botName + ".py")))
    loop.run_forever()