import asyncio
import json
import shutil
import sys
import random
import tempfile
import zipfile
import zlib
from base64 import b64decode, b64encode
from pathlib import Path
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands
import numpy

from chicorobot import autocomplete
from chicorobot.sprites import *
from chicorobot.assets import *
from chicorobot.utils import *

async def setup(bot):
    await bot.add_cog(SpriteCog(bot))
    bot.SpriteModificationView = SpriteModificationView(animated=False)

def del_temp(temp):
    if temp:
        try:
            shutil.rmtree(temp)
        except PermissionError:
            print("Failed to delete file.")
        else:
            print(f"Deleted temp: {str(temp)}")

default_data = {
    "user": 0,
    "sprite": "sprMarioRpg", "animated": False, "animation_name": None, "animation_fps": 10,
    "crop_transparency": True, "use_frame": None, "output_zip": False,
    "colour_1": "#ffffff", "colour_2": "#ffffff", "colour_3": "#ffffff"
}

async def get_data(msg):
    i = msg.content.index("$") + 1
    data1 = msg.content[i:msg.content.index("$", i)]
    data1 = b64decode(data1.encode("utf-8"))
    data1 = zlib.decompress(data1).decode("utf-8")
    data1 = json.loads(data1)

    data = default_data.copy()
    data.update(data1)
    return data

class RetryModalView(discord.ui.View):
    def __init__(self, modal):
        super().__init__()
        self.modal = modal
    
    @discord.ui.button(label="Re-enter", emoji="🔁")
    async def reenter(self, interaction, button):
        for i in self.modal.children:
            i.default = i.value
        await interaction.response.send_modal(self.modal)
        await (await interaction.original_response()).delete()

class SpriteInputModal(discord.ui.Modal, title="Input!"):
    def __init__(self, input_type: int, data: dict, message: discord.Message):
        super().__init__()
        self.message = message
        self.input_type = input_type
        self.data = data
        self.original_user = self.data.pop("user")
        if input_type == 0: # set_frame
            frames = sprites[data["sprite"]].layer.get_frames()
            minn, maxn = 0, 0
            if isinstance(frames[0], int):
                minn, maxn = min(frames), max(frames)
            self.frame_range = [minn, maxn]
            self.frame = discord.ui.TextInput(label=f"Frame Number ({minn} to {maxn})", default=data["use_frame"])
            self.add_item(self.frame)
        elif input_type == 1: # set_colours
            self.colour_1 = discord.ui.TextInput(label="Colour 1", default=data["colour_1"])
            self.colour_2 = discord.ui.TextInput(label="Colour 2", default=data["colour_2"])
            self.colour_3 = discord.ui.TextInput(label="Colour 3", default=data["colour_3"])
            [self.add_item(i) for i in [self.colour_1, self.colour_2, self.colour_3]]
        elif input_type == 2: # other_options
            self.animation_name = discord.ui.TextInput(label="Animation Name (or `none`)", default=str(data["animation_name"]))
            self.animation_fps = discord.ui.TextInput(label="Animation FPS", default=data["animation_fps"])
            self.output_zip = discord.ui.TextInput(label="Output ZIP (`true` or `false`)", default=str(data["output_zip"]))
            self.crop_transparency = discord.ui.TextInput(label="Crop Transparency (`true` or `false`)", default=str(data["crop_transparency"]))
            [self.add_item(i) for i in [self.animation_name, self.animation_fps, self.output_zip, self.crop_transparency]]

    async def on_submit(self, interaction):
        if self.input_type == 0: # set_frame
            self.data["animated"] = False
            self.data["output_zip"] = False
            async def invalid_number(not_range=False): 
                if self.frame.label.endswith("Invalid Number"):
                    if not_range:
                        self.frame.label = self.frame.label.replace("Invalid Number", "Out of Range")
                elif self.frame.label.endswith("Out of Range"):
                    if not not_range:
                        self.frame.label = self.frame.label.replace("Out of Range", "Invalid Number")
                elif not_range:
                    self.frame.label += " - Out of Range"
                else:
                    self.frame.label += " - Invalid Number"
                await interaction.response.send_message("Out of Range" if not_range else "Invalid Number", ephemeral=True, view=RetryModalView(self))
            try:
                f = int(self.frame.value)
            except ValueError:
                return await invalid_number()
            if not (f >= self.frame_range[0] and f <= self.frame_range[1]):
                return await invalid_number(True)
            self.data["use_frame"] = f
        elif self.input_type == 1: # set_colours
            hex_fail = False
            for i, item in enumerate(self.children):
                v = item.value.lstrip("#")
                try:
                    int(v, base=16)
                except ValueError:
                    v = "epic hex fail"
                if len(v) != 6: # epic hex falure
                    if not item.label.endswith("Hex"):
                        item.label = item.label + " - Invalid Hex"
                    hex_fail = True
                else: # epic hex success
                    if item.label.endswith("Hex"):
                        item.label = item.label.replace(" - Invalid Hex", "") # In case the user had an epic hex fail previously and has another, separate one
                    self.data[f"colour_{i+1}"] = item.value
            if hex_fail:
                return await interaction.response.send_message("Invalid Hex", ephemeral=True, view=RetryModalView(self))
        elif self.input_type == 2:
            if self.animation_name.value.lower() == "none":
                self.data["animation_name"] = None
            else:
                self.data["animation_name"] = self.animation_name.value
            try:
                self.data["animation_fps"] = int(self.animation_fps.value)
            except ValueError:
                self.animation_fps.label = "Animation FPS - Invalid Number"
                return await interaction.response.send_message("Invalid Number", ephemeral=True, view=RetryModalView(self))
            self.data["output_zip"] = self.output_zip.value.lower().strip() == "true" # Default to false on anything else
            self.data["crop_transparency"] = self.crop_transparency.value.lower().strip() != "false" # Default to true on anything else
        out, file, msg, temp = await create_sprite(interaction, **self.data)
        if interaction.user.id == self.original_user: # original user
            await msg.delete()
            await self.message.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        else:
            await msg.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        file.close()
        del_temp(temp)

class SpriteModificationView(discord.ui.View):
    def __init__(self, animated):
        super().__init__(timeout=None)
        if animated:
            self.animate.label = "Make Image"
            self.animate.emoji = "🖼️"

    async def send_modal(self, interaction, type):
        data = await get_data(interaction.message)
        modal = SpriteInputModal(type, data, interaction.message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Make Animated", emoji="📽️", custom_id="spritemod:animate")
    async def animate(self, interaction, button):
        data = await get_data(interaction.message)
        user = data["user"]
        data.pop("user")
        data["animated"] = not data["animated"]
        data["output_zip"] = False
        out, file, msg, temp = await create_sprite(interaction, **data)
        if interaction.user.id == user: # original user
            await msg.delete()
            await interaction.message.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        else:
            await msg.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        file.close()
        del_temp(temp)

    @discord.ui.button(label="Change Frame", emoji="🎞️", custom_id="spritemod:set_frame")
    async def set_frame(self, interaction, button):
        await self.send_modal(interaction, 0)

    @discord.ui.button(label="Set Colours", emoji="🖌️", custom_id="spritemod:set_colours")
    async def set_colours(self, interaction, button):
        await self.send_modal(interaction, 1)

    @discord.ui.button(label="Other Options", emoji="⚙️", custom_id="spritemod:other_options")
    async def other_options(self, interaction, button):
        await self.send_modal(interaction, 2)

async def create_sprite(
        interaction: discord.Interaction,
        sprite: str, animated: bool=False, animation_name: str=None, animation_fps: int=10,
        crop_transparency: bool=True, use_frame: str=None, output_zip: bool=False,
        colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None
    ):
    await interaction.response.defer()
    sprite = sprite.replace(" ","_")

    colour_3 = colour_3 or colour_1
    
    if isinstance(colour_1, str): # Users COULD put any number of #'s and it'd be a valid colour because of lstrip so to not break anything i'll make sure it's only 1
        colour_1 = "#" + colour_1.lstrip("#")
    if isinstance(colour_2, str):
        colour_2 = "#" + colour_2.lstrip("#")
    if isinstance(colour_3, str):
        colour_3 = "#" + colour_3.lstrip("#")

    if output_zip and not animated:
        animated = True

    animation_fps = round(animation_fps)
    animation_fps = min(max(animation_fps, 1), 50)

    if (animated and not output_zip) and not imagemagick:
        await interaction.followup.send(content="Animated sprites are unavailable, making non animated version.")
        animated = False
    
    if sprite.lower() == "random":
        sprite = random.choice(sprites.sprites())
    
    ims = None
    if sprite not in sprites.sprites():
        sprite = to_titlecase(sprite)
    name = sprite
    sprite = sprites[name]

    layers = sprite.get_layers()
    
    if name.endswith("_A"):
        sproot = "_".join(name.split("_")[:-1]) + "_"
        layers += [sprites[i]["1"] for i in [sproot+"B",sproot+"ear"]]
    
    frames = sprite.layer.get_frames()

    wasanimated = False
    if len(frames) == 1 and animated:
        animated = False
        wasanimated = True
    
    content = "Making Image"
    if animated:
        content += "s and saving to PNG (1/2)"
    elif wasanimated:
        content += " (single frame sprite, does not need to be animated)"
    msg = await interaction.followup.send(content=content)

    frameN = 0
    if animated: # Create temp for frame saving
        temp = tempfile.mkdtemp()
        temp = Path(temp)
        print(f"Making temp: {str(temp)}")

    if use_frame and not animated: # User specified frame
        f = 0
        try:
            f = int(use_frame)
            namestr = False
        except ValueError:
            f = use_frame
            namestr = True
        if namestr and sprite.layer.frames: # The gave us a str but we only have numbered frames
            await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
            raise errors.InvalidFrame() # Can't return without 4 vars so i'll just do an error that gets ignored
        elif not namestr and not sprite.layer.frames: # They gave us a number but we only have string frames
            await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
            raise errors.InvalidFrame()
        if namestr:
            if f not in sprite.layer.get_frames():
                await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
                raise errors.InvalidFrame()
            frames = [f]
        else:
            if f >= len(frames):
                await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
                raise errors.InvalidFrame()
            frames = [f]

    crop = None

    for frame in frames:
        im = await sprite.layer.load_frame(frame, colour=colour_1)
        for i in sorted(layers[1:]):
            if isinstance(i, Layer):
                layer = i
            else:
                layer = sprite[i]
            if frame in layer.get_frames():
                sproot = layer.root
                f = frame
                if layer.offset:
                    f -= layer.offset
                col = colour_2 if i == "2" else colour_3
                im2 = await layer.load_frame(f, anim=animation_name, colour=col)
                im2n = numpy.array(im2)
                im2n = numpy.where(im2n[:, :, 3] > 0)
                if im2n[0].size == 0 and im2n[1].size == 0:
                    im2 = await layer.load_frame(f, colour=col)
                im.alpha_composite(im2)
        if crop_transparency:
            imnp = numpy.array(im)
            imnp = numpy.where(imnp[:, :, 3] > 0) # Non transparent pixels
            try:
                if not crop:
                    crop  = [imnp[1].min(), imnp[0].min(), imnp[1].max(), imnp[0].max()]
                else:
                    crop[0] = min(crop[0], imnp[1].min())
                    crop[1] = min(crop[1], imnp[0].min())
                    crop[2] = max(crop[2], imnp[1].max())
                    crop[3] = max(crop[3], imnp[0].max())
            except ValueError:
                pass # Blank Image
        if animated:
            im.save(temp / f"{frameN:03}.gif")
            frameN += 1
        else:
            if crop_transparency and crop:
                ims = im.crop(box=crop)
            else:
                ims = im
            break

    data = {
        "user": interaction.user.id,
        "sprite": name, "animated": animated, "animation_name": animation_name, "animation_fps": animation_fps,
        "crop_transparency": crop_transparency, "use_frame": use_frame, "output_zip": output_zip,
        "colour_1": colour_1, "colour_2": colour_2, "colour_3": colour_3
    }

    for i in default_data.keys():
        if data[i] == default_data[i]:
            data.pop(i)

    data = json.dumps(data, separators=(",",":"))
    data = zlib.compress(data.encode("utf-8"))
    data = b64encode(data).decode("utf-8")
    data = f"[](${data}$)"

    if not animated:
        imbyte = BytesIO()
        ims.save(imbyte, "PNG")
        imbyte.seek(0)
        out = f"{name} frame `{frames[0]}`{' (one frame sprite, animation not required)' if wasanimated else ''}:{data}\n"
        file = discord.File(imbyte, f"{name}..png")
        return out, file, msg, None

    giferror = False

    if animated and not output_zip:
        await msg.edit(content="Converting PNGs to GIF (2/2)")
        addcrop = f"--crop {crop[0]},{crop[1]}-{crop[2]},{crop[3]} " if crop_transparency else ""
        process = await asyncio.create_subprocess_shell(
            f"{gifsicle} --delay {int(1/animation_fps*100)} --disposal bg --loopcount=0 {addcrop}{temp / '*.gif'}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        gifdata = BytesIO(stdout)
        if process.returncode != 0: # Error
            print(f"GIF CONVERSION ERROR: {stdout.decode()}")
            giferror = True
        else:
            out = f"{name} at {animation_fps} fps:{data}\n"
            file = discord.File(gifdata, f"{name}.gif")
            return out, file, msg, temp

    if animated and output_zip:
        await msg.edit(content=f"{'GIF Conversion failed, ' if giferror else ''}Zipping PNGs (2/2)")
        f = BytesIO()
        with zipfile.ZipFile(f, "x") as zipf:
            for i in temp.glob("*.png"):
                zipf.write(i, i.relative_to(temp))
        f.seek(0)
        file = discord.File(f, f"{name}.zip")
        out = f"{name}:{data}" if not giferror else f"{name} (Zip, GIF conversion failed):{data}\n"
        return out, file, msg, temp

class SpriteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name="Get Sprite Info", callback=self.sprite_info, extras={"ephemeral": True})
        bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @app_commands.command(description="Show a sprite.")
    @app_commands.describe(
        sprite="The sprite to show", animated="If True, sends an animated gif", animation_name="Name of the animation to use, get a list of them for a sprite using /animations.", animation_fps="If animated. Sets the FPS of the animation (max 50)",
        crop_transparency="Removes any blank area around the image", use_frame="If not animated, choose a frame of the sprite to send (starts at 0)", output_zip="Outputs animation as a zip of PNGs for high quality."
    )
    @app_commands.autocomplete(sprite=autocomplete.sprite)
    async def sprite(
            self, interaction: discord.Interaction,
            sprite: str, animated: bool=False, animation_name: str=None, animation_fps: int=10,
            crop_transparency: bool=True, use_frame: str=None, output_zip: bool=False,
            colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None
        ):
        out, file, msg, temp = await create_sprite(
            interaction,
            sprite, animated, animation_name, animation_fps,
            crop_transparency, use_frame, output_zip,
            colour_1, colour_2, colour_3
        )
        await msg.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None))) # idk if i wanna add create_sprite returning if it is animated (it can change with 1 frame sprites) but there being a temp is a 100% way to know
        file.close()
        del_temp(temp)

    # Get Sprite Info Context Menu
    async def sprite_info(self, interaction, message: discord.Message):
        try:
            data = await get_data(message)
        except ValueError:
            return await interaction.response.send_message("Sprite not found in the message.", ephemeral=True)
        embed = discord.Embed(title="Sprite Info")
        for key in ["user", "sprite", "use_frame", "output_zip", "animated", "animation_name", "animation_fps", "colour_1", "colour_2", "colour_3"]:
            value = data[key]
            if key == "user":
                value = f"<@{value}>"
            else:
                value = f"`{value}`"
            embed.add_field(name=to_titlecase(key.replace("_", " ")), value=value, inline=(key != "user"))
        await interaction.response.send_message(embed=embed, ephemeral=True)
