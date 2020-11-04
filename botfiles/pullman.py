import discord
import asyncio
from .botmodules import TTRPGBot, SimpleVoteBot

#importlib.reload(generic)
class PullmanBot(TTRPGBot, SimpleVoteBot):
	def getName(self):
		return "pullman"

	def __init__(self, prefix="!"):
		super().__init__(prefix, "ALL ABOARD!", "TRAIN'S LEAVING THE STATION!")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Pullman Bot')
	parser.add_argument("token", type=str, nargs=1)
	args = parser.parse_args()
	pullman = PullmanBot()
	pullman.run(args.token[0])
