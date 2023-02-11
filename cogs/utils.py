import random
import textwrap
import traceback
from contextlib import redirect_stdout
from io import BytesIO, StringIO

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

from chicorobot import autocomplete
from chicorobot.assets import *
from chicorobot.sprites import *
from chicorobot.utils import to_titlecase

async def setup(bot):
    await bot.add_cog(Utils(bot))

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Lists animations for a specific sprite")
    @app_commands.autocomplete(sprite=autocomplete.animations_sprite)
    async def animations(self, interaction: discord.Interaction, sprite: str):
        anims = []
        for layer in sprites[sprite].get_layers():
            if sprites[sprite][layer].anim_root:
                anims += list(sprites[sprite][layer].anim_root)
        await interaction.response.send_message(content=f"{sprite} animations: `{'`, `'.join(anims)}`")

    @app_commands.command(description="Lists frames for a specific sprite")
    @app_commands.autocomplete(sprite=autocomplete.sprite)
    async def frames(self, interaction: discord.Interaction, sprite: str):
        if sprite not in sprites.sprites():
            await interaction.response.send_message(content="Incorrect Sprite")
            return
        frames = sprites[sprite].layer.get_frames()
        numbers = []
        strings = []
        for frame in frames: # This is kinda stupid with numbered frames
            try:
                numbers.append(int(frame))
            except ValueError:
                strings.append(frame)
        out = ""
        if numbers:
            out += f"Frames {min(numbers)} to {max(numbers)}\n"
        if strings:
            out += f"Frames: `{'`, `'.join(strings)}`"
        if not out:
            out = "None"
        await interaction.response.send_message(content=out)

    @app_commands.command(description="Get a palette from the game!")
    @app_commands.describe(
        area_name="Name of an area from the game. Not required if code_name specified.",
        code_name="Name of a palette in the games code. Not required if area_name specified."
    )
    @app_commands.autocomplete(area_name=autocomplete.area_name, code_name=autocomplete.code_name)
    async def palette(self, interaction: discord.Interaction, area_name: str=None, code_name: str="Random"):
        if area_name:
            area_name = to_titlecase(area_name)

            if area_name == "Random":
                area_name = random.choice([i for i in paletteAliases.keys()])
            
            if area_name in paletteAliases:
                palette = paletteAliases[area_name]
                palette_text = f"`{area_name}` (`{palette}`)"
            else:
                await interaction.response.send_message(f"<:Pizza_Awkward:967482807960105062> Area palette `{area_name}` not found.")
                return

        else:
            palette = code_name.lower()
            palette_text = f"`{code_name.lower()}`"
            
            if palette == "random":
                palette = random.choice(list(palettes.keys()))
                palette_text = f"`{palette}`"
        
            if palette not in palettes.keys():
                await interaction.response.send_message(f"<:Pizza_Awkward:967482807960105062> Code palette `{code_name}` not found.")
                return
        
        colours = [tuple(c) for c in palettes[palette]]
        width = 63
        im = Image.new("RGB", (width*len(colours), 20), colours[0])
        for i, colour in enumerate(colours):
            if i == 0:
                continue
            im.paste(Image.new("RGB", (width, 20), colour), box=(width*i, 0))
        
        fp = BytesIO()
        im.save(fp, format="PNG")
        fp.seek(0)
        file = discord.File(fp, filename="palette.png")
        await interaction.response.send_message(f"{palette_text}\n`{'`, `'.join([('#%02x%02x%02x' % i) for i in colours])}`", file=file)

    @app_commands.command(description="Send a picture of hair to name.")
    async def hair(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="https://media.discordapp.net/attachments/967965561361428490/1004109210151301120/unknown.png", ephemeral=True)

    # Owner Only

    # Checks if user is owner
    def is_owner():
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id == interaction.client.ownerid
        return app_commands.check(predicate)

    @app_commands.command(description="Death.")
    @is_owner()
    async def die(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="I hath been slayn.")
        await self.bot.close()

    @app_commands.command(description="Sink.")
    @is_owner()
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.bot.tree.copy_global_to(guild=self.bot.guild)
        await self.bot.tree.sync(guild=self.bot.guild)
        await interaction.followup.send("Sunk.", ephemeral=True)


    @app_commands.command(description="Realods a cog")
    @is_owner()
    @app_commands.autocomplete(cog=autocomplete.cog)
    async def reload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            await interaction.response.send_message("Error")
            raise e
        else:
            await interaction.response.send_message(f"Reloaded {cog}")

    # Modal for the exec command input and processing.
    class ExecModal(discord.ui.Modal, title="Execute Code!"):
        code = discord.ui.TextInput(label="Code!", style=discord.TextStyle.long)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()

            # Reworked from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L216-L261

            env = {
                "bot": interaction.client,
                "interaction": interaction,
                "guild": interaction.guild,
                "channel": interaction.channel,
                "user": interaction.user,
                "_": interaction.client.previous_exec
            }

            env.update(globals())

            execcode = textwrap.indent(self.code.value, "    ")
            execcode = f"async def func():\n{execcode}"

            try:
                exec(execcode, env)
            except Exception as error:
                await interaction.followup.send(f"```py\n{error.__class__.__name__}: {error}\n```", ephemeral=True)
                raise error
                return

            await interaction.followup.send(f"Executing:\n```py\n{self.code.value}\n```", ephemeral=True)

            stdout = StringIO()
            func = env["func"]
            try:
                with redirect_stdout(stdout):
                    value = await func()
            except Exception as error:
                out = stdout.getvalue()
                await interaction.followup.send(f"ERROR:\n```py\n{out}\n{error.__class__.__name__}: {error}```", ephemeral=True)
            else:
                ephemeral = False
                if isinstance(value, (tuple, list)):
                    ephemeral = value[-1]
                    if len(value) > 2:
                        value = value[0:-1]
                    else:
                        value = value[0]
                out = stdout.getvalue()
                if out:
                    await interaction.followup.send(f"```py\n{out}\n```", ephemeral=True)
                if value:
                    interaction.client.previous_exec = value
                    await interaction.followup.send(value, ephemeral=ephemeral)

    # Just sends the exec modal
    @app_commands.command(name="exec", description="HACKING CODING.")
    @is_owner()
    async def execute(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.ExecModal())

    # Sends last error
    @app_commands.command(name="get_error", description="Shows the previous error :skull:")
    @is_owner()
    async def get_last_error(self, interaction: discord.Interaction):
        if self.bot.last_error:
            error = self.bot.last_error
            text = ""
            for i in traceback.format_exception(error, value=error, tb=None):
                if i.startswith("\nThe above"):
                    text = ""
                    continue
                text += i
            await interaction.response.send_message(f"```{text[:1994]}```", ephemeral=True)
        else:
            await interaction.response.send_message("No error.", ephemeral=True)
