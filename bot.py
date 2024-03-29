import random
import shutil
import sys
import logging
from pathlib import Path

import PIL
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
        self.last_error = None
        self.SpriteModificationView = False
        self.RandomRepeatView = False
        self.HareRandomRepeatView = False

    async def setup_hook(self):
        if not Path("userdata/").exists():
            Path("userdata/").mkdir()

        await bot.load_extension("cogs.utils")
        await bot.load_extension("cogs.sprite")
        await bot.load_extension("cogs.dog")
        await bot.load_extension("cogs.hare")
        await bot.load_extension("cogs.save")

        if len(sys.argv) > 1 and "test" in sys.argv: # just for me to test easily :D
            self.guild = discord.Object(473976215301128193) # msmg
        else:
            self.guild = None

        if len(sys.argv) > 1 and "sync" in sys.argv:
            if self.guild:
                self.tree.copy_global_to(guild=self.guild)
            await self.tree.sync(guild=self.guild)
        
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
    ephemeral = interaction.command.extras["ephemeral"] if "ephemeral" in interaction.command.extras else False
    error = getattr(error, "original", error)
    
    send = interaction.response.send_message if not interaction.response.is_done() else interaction.followup.send
    
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("<:Pizza_Angry:967482622194372650> You're not allowed to do that.", ephemeral=True)
    elif isinstance(error, errors.ColourError):
        await send("You inputted a colour wrong!", ephemeral=ephemeral)
    elif isinstance(error, errors.SpriteNotFound):
        await send(f"Sprite `{error.sprite}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.FrameNotFound):
        await send(f"Frame `{error.frame}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.AnimationNotFound):
        await send(f"Animation `{error.animation}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.ClothingNotFound):
        await send(f"Clothing `{error.clothing}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.HatNotFound):
        await send(f"Hat `{error.hat}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.HairNotFound):
        await send(f"Hair `{error.hair}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, errors.ExpressionNotFound):
        await send(f"Expression `{error.expression}` could not be found.", ephemeral=ephemeral)
    elif isinstance(error, (errors.InvalidFrame, errors.GifError, errors.PropAnimationError)):
        return
    elif isinstance(error, errors.SaveNotUploaded):
        await send("Your save data has not been uploaded yet. Use `/save upload` to do that!")
    elif isinstance(error, PIL.UnidentifiedImageError):
        await send("Image file not recognised! Make sure it's a PNG.")
    else:
        await send("<:Pizza_Depressaroli:967482279670718474> Something went wrong.", ephemeral=ephemeral)
        bot.last_error = error
        raise error

# run.
bot.run(TOKEN)
