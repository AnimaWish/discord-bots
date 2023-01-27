import discord
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


# if __name__ == "__main__":
#     bots = {
#         # "philippe": botfiles.PhilippeBot(),
#         # "mettaton": botfiles.MettatonBot(),
#         # "zenyatta": botfiles.ZenyattaBot(),
#         # "gyoshin":  botfiles.GyoshinBot(),

#         "lif":  botfiles.LifBot()
#     }

#     loop = asyncio.get_event_loop()
#     for botName in bots.keys():
#         loop.create_task(bots[botName].client.start(fetchToken(botName + ".py")))
#     loop.run_forever()

async def main():
    normalIntents = discord.Intents().all()
    normalIntents.bans = False
    normalIntents.invites = False
    normalIntents.presences = False
    normalIntents.typing = False
    normalIntents.auto_moderation = False

    bots = {
        "philippe": botfiles.PhilippeBot(intents=normalIntents),
        "mettaton": botfiles.MettatonBot(intents=normalIntents),
        "zenyatta": botfiles.ZenyattaBot(intents=normalIntents),
        "gyoshin":  botfiles.GyoshinBot(intents=normalIntents),
        "lif":      botfiles.LifBot(intents=normalIntents),
        "pullman":  botfiles.PullmanBot(intents=normalIntents),
    }

    async with asyncio.TaskGroup() as tg:
        for botName in bots.keys():
            tg.create_task(runClient(bots[botName]))

async def runClient(client):
    botName = client.getName()
    token = fetchToken(botName + ".py")
    # async with client: # unnecessary?
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())
