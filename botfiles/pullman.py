import discord
import asyncio
from .botmodules import TTRPGBot, SimpleVoteBot

#importlib.reload(generic)
class PullmanBot(TTRPGBot, SimpleVoteBot):
	def getName(self):
		return "pullman"

	def __init__(self, prefix="!", *, intents, **options):
		super().__init__(prefix, "ALL ABOARD!", "TRAIN'S LEAVING THE STATION!", intents=intents, options=options)
