import random
import textwrap
import traceback
from contextlib import redirect_stdout
from io import BytesIO, StringIO

import numpy
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

    @app_commands.command(description="Lists and shows info about animations for a specific sprite")
    @app_commands.autocomplete(sprite=autocomplete.animations_sprite)
    async def animations(self, interaction: discord.Interaction, sprite: str):
        if sprite not in prop_animations:
            sprite = to_titlecase(sprite)
            if sprite not in prop_animations:
                return await interaction.response.send_message(content=f"`{sprite}` has no animations.")
        anims = list(prop_animations[sprite].keys())
        outl = [["Anim", "Regularly loops/goes to", "Frames"]]
        sound = False
        for anim in anims:
            outl.append([f"'{anim}'"])
            loop = prop_animations[sprite][anim]["loop"]
            if loop == 1:
                outl[-1].append("Loops")
            elif loop == 0:
                outl[-1].append("Doesn't loop")
            elif isinstance(loop, str):
                outl[-1].append(f"Goes to '{loop}'")
            elif isinstance(loop, list):
                chances = {}
                total = 0
                for i in loop:
                    if i not in chances:
                        chances[i] = 0
                    chances[i] += 1
                    total += 1
                outl[-1].append("Goes to one of ")
                outl[-1][-1] += ', '.join([f"'{i}': {round(v/total*100)}%" for i, v in chances.items()])
            start = prop_animations[sprite][anim]['frames']['start']
            end = prop_animations[sprite][anim]['frames']['end']
            if start != end:
                outl[-1].append(f"Frames '{start}' to '{end}'")
            else:
                outl[-1].append(f"Frame '{start}'")
            sounds = prop_animations[sprite][anim]['frames']['sounds']
            if sounds != -1:
                soundlist = list(sounds.values())
                soundlist = "', '".join(soundlist)
                outl[-1].append(f"Plays: '{soundlist}'")
                sound = True
        longest1 = max([len(i[0]) for i in outl])
        longest2 = max([len(i[1]) for i in outl])
        longest3 = max([len(i[2]) for i in outl])
        if sound:
            outl[0].append("Sound(s)")
        out = "`"
        line1 = True
        for l in outl:
            out += f"{l[0]: >{longest1}} | "
            out += f"{l[1]: >{longest2}} | "
            out += f"{l[2]: >{longest3}}{' |' if sound else ''}"
            if len(l) > 3:
                out += f" {l[3]}"
            if line1:
                line1 = False
                out += "`\n```"
            else:
                out += "\n"
        out += "```"
        if len(out) > 2000:
            fileout = BytesIO()
            fileout.write(out.replace("`", "").encode("utf-8"))
            fileout.seek(0)
            file = discord.File(fileout, filename=f"{sprite}_animations.txt")
            await interaction.response.send_message(content="Animations too long, sent as file.", file=file)
            file.close()
        else:
            await interaction.response.send_message(content=f"`{sprite}` animations:\n{out}")

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

    @app_commands.command(description="Sends preview images of dog parts that aren't named in-game.")
    async def preview_dog(self, interaction: discord.Interaction):
        embeds = []
        embeds.append(discord.Embed(title="Hair Preview:"))
        embeds[-1].set_image(url="https://media.discordapp.net/attachments/967965561361428490/1004109210151301120/unknown.png")
        embeds.append(discord.Embed(title="Expressions Preview:"))
        embeds[-1].set_image(url="https://media.discordapp.net/attachments/1073696482827440218/1116902058491117628/image.png")
        await interaction.response.send_message(embeds=embeds, ephemeral=True)

    @app_commands.command(description="Identifies Chicory palette colors from an image.")
    @app_commands.describe(image="The Image to get the colors from.", eyestrain_mode="The eyestrain mode used in Chicory. Use 'detect' to try to detect it.", color_threshold="Amount of the image the color has to take up to be considered. (min 0.1)")
    @app_commands.choices(eyestrain_mode=[
        app_commands.Choice(name="None", value=0),
        app_commands.Choice(name="Default", value=1),
        app_commands.Choice(name="Lots", value=2),
        app_commands.Choice(name="Detect", value=3)
    ])
    async def identify_colors(self, interaction: discord.Interaction, image: discord.Attachment, eyestrain_mode: app_commands.Choice[int]=3, color_threshold: float=1.0):
        await interaction.response.defer(thinking=True)

        color_threshold = min(0.1, max(10, color_threshold))
        percent_threshold = color_threshold*0.5

        if isinstance(eyestrain_mode, app_commands.Choice):
            eyestrain_mode = eyestrain_mode.value
        
        im = BytesIO()
        await image.save(im)
        im = Image.open(im)
        im = im.convert("RGB")

        pixel_threshold = (im.width * im.height) * (percent_threshold / 100)

        im_np = numpy.array(im)

        auto_fail = False

        if eyestrain_mode == 3:
            if (numpy.all(im_np == (255, 245, 237), axis=-1)).any():
                eyestrain_mode = 1 # Default eyestrain white in image
            elif (numpy.all(im_np == (255, 255, 255), axis=-1)).any():
                eyestrain_mode = 0 # White in image, no eyestrain mode (this is second because it's detecting white in default images even though THERE ISN'T ANY IM GOING INSANE)
            elif (numpy.all(im_np == (240, 197, 150), axis=-1)).any():
                eyestrain_mode = 2 # Lots eyestrain white in image
            else:
                eyestrain_mode = 0
                auto_fail = True

        if eyestrain_mode > 0:
            im_np = numpy.float64(im_np)
            if eyestrain_mode == 1:
                r_mult = 1
                g_mult = 0.941
                b_mult = 0.847
                im_np[:, :, 1] -= 0.02 * 255 # g
                im_np[:, :, 2] -= 0.082 * 255 # b
            elif eyestrain_mode == 2:
                r_mult = 0.941
                g_mult = 0.772
                b_mult = 0.588
            im_np[:, :, 0] /= r_mult
            im_np[:, :, 1] /= g_mult
            im_np[:, :, 2] /= b_mult
            im_np = numpy.rint(im_np)
            im_np = numpy.clip(im_np, 0, 255)
            im_np = numpy.uint8(im_np)
        im_np_flat = numpy.reshape(im_np, (-1, im_np.shape[2]))
        _, indexes, counts = numpy.unique(im_np_flat, axis=0, return_index=True, return_counts=True)
        cols = numpy.extract(counts > pixel_threshold, indexes)
        cols = numpy.take(im_np_flat, cols, axis=0)
        chicory_cols = {}
        for col in cols:
            col = col.tolist()
            for palette in palettes.keys():
                for pcol in palettes[palette]:
                    match = True
                    for i in range(3):
                        if not (col[i] - 1 <= pcol[i] and col[i] + 1 >= pcol[i]): # Range of 1 around each color rgb because of rounding when undoing shader 
                            match = False
                            break
                    if match:
                        if palette not in chicory_cols:
                            chicory_cols[palette] = []
                        if tuple(pcol) not in chicory_cols[palette]:
                            chicory_cols[palette].append(tuple(pcol))
        palette_names = {v: k for k, v in paletteAliases.items()}
        if chicory_cols:
            out = "Detected Colors:\n"
            for palette in chicory_cols:
                pcols = '`, `'.join(['#%02x%02x%02x' % c for c in chicory_cols[palette]])
                if palette in palette_names:
                    name = palette_names[palette]
                else:
                    name = to_titlecase(palette)
                out += f"{name} - `{pcols}`\n"
            width = 63
            outim = Image.new("RGBA", (width*4, 20*len(chicory_cols.keys())), (255,255,255, 0))
            h = 0
            for pcols in chicory_cols.values():
                for i, pcol in enumerate(pcols):
                    cim = Image.new("RGBA", (width, 20), tuple([i for i in pcol] + [255]))
                    outim.paste(cim, box=(width*i, 20*h))
                h += 1
            outb = BytesIO()
            outim.save(outb, format="PNG")
            outb.seek(0)
            file = discord.File(outb, filename="colors.png")
            outb2 = BytesIO()
            Image.fromarray(im_np).save(outb2, format="PNG")
            outb2.seek(0)
            file2 = discord.File(outb2, filename="image.png")
            embeds = [discord.Embed().set_image(url="attachment://colors.png"), discord.Embed().set_image(url="attachment://image.png")]
            await interaction.followup.send(out, files=[file, file2], embeds=embeds)
        else:
            eyestrain_types = ["None", "Default", "Lots"]
            await interaction.followup.send(f"No Chicory colors detected. If this is wrong try one or more of the following:\n- Using an eyestrain mode other than `{eyestrain_types[eyestrain_mode] if not auto_fail else f'Detect/{eyestrain_types[eyestrain_mode]}'}`\n- Using a lower color_threshold\n- Crop the image more.\nSometimes it can't detect colors if:\n- The picture is taken in a dark area\n- The paint is on a non climbable wall or on water.")


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
        if self.bot.guild:
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
    @app_commands.command(name="get_error", description="Shows the previous error :skull:", extras={"ephemeral": True})
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
