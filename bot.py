import random
import shutil
import sys
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from chicorobot import errors


#Get bot token
def no_token():
    logging.info("TOKEN NOT FOUND!! Put it as the first line in TOKEN.txt")
    sys.exit()

if not Path("TOKEN.txt").exists():
    no_token()
with Path("TOKEN.txt").open("r") as f:
    TOKEN = f.readline().rstrip()
if not TOKEN:
    no_token()

# Discord bot
class Chicorobot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__("", intents=intents)
        self.previous_exec = None
        self.ownerid = 0

    async def setup_hook(self):
        await bot.load_extension("cogs.utils")
        await bot.load_extension("cogs.sprite")
        await bot.load_extension("cogs.dog")

        #guild = discord.Object(473976215301128193) # msmg
        guild = discord.Object(947898290735833128)

        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)

        self.add_view(bot.SpriteModificationView)
        
        appinfo = await bot.application_info()
        bot.ownerid = appinfo.owner.id

bot = Chicorobot()
tree = bot.tree

# Discord Events and Error Handling
@bot.event
async def on_ready():
    print("LOGGED IN!")

@bot.event
async def on_message(message): # Overide default Bot on_message so text commands aren't processed
    pass

@tree.error
async def command_error(interaction: discord.Interaction, error):
    error = getattr(error, "original", error)
    
    send = interaction.response.send_message if not interaction.response.is_done() else interaction.followup.send
    
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("<:Pizza_Angry:967482622194372650> You're not allowed to do that.", ephemeral=True)
    elif isinstance(error, errors.ColourError):
        await send("You inputted a colour wrong!")
    elif isinstance(error, errors.SpriteNotFound):
        await send(f"Sprite `{error.sprite}` could not be found.")
    elif isinstance(error, errors.LayerNotFound):
        await send(f"Layer `{error.layer}` could not be found.")
    elif isinstance(error, errors.FrameNotFound):
        await send(f"Frame `{error.frame}` could not be found.")
    else:
        await send("<:Pizza_Depressaroli:967482279670718474> Something went wrong.")
        raise error

# run.
bot.run(TOKEN)
