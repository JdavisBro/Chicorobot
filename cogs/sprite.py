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

from chicorobot import autocomplete, errors
from chicorobot.sprites import *
from chicorobot.assets import *
from chicorobot.utils import *

async def setup(bot):
    await bot.add_cog(SpriteCog(bot))

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
    "sprite": "sprMarioRpg", "animated": False, "animation_seq": None, "animation_fps": 10, "animation_speed": 1,
    "crop_transparency": True, "use_frame": None, "output_zip": False,
    "colour_1": "#ffffff", "colour_2": "#ffffff", "colour_3": "#ffffff",
    "random": None
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
    def __init__(self, modal, err_msg: list):
        super().__init__()
        self.input_type = modal.input_type
        self.data = modal.data
        self.data["user"] = modal.original_user
        self.message = modal.message
        self.err_msg = err_msg
    
    @discord.ui.button(label="Re-enter", emoji="🔀")
    async def reenter(self, interaction, button):
        await interaction.response.send_modal(SpriteInputModal(self.input_type, self.data, self.message, self.err_msg))

class SpriteInputModal(discord.ui.Modal, title="Input!"):
    def __init__(self, input_type: int, data: dict, message: discord.Message, err_msg: list=[None,None,None,None]):
        super().__init__()
        self.message = message
        self.input_type = input_type
        self.data = data
        self.original_user = self.data.pop("user")
        if "random" in self.data:
            self.data.pop("random")
        def add_error(label, error):
            if error:
                return label + " - " + error
            return label
        if input_type == 0: # set_frame
            frames = sprites[data["sprite"]].layer.get_frames()
            minn, maxn = 0, 0
            if isinstance(frames[0], int):
                minn, maxn = min(frames), max(frames)
            self.frame_range = [minn, maxn]
            self.frame = discord.ui.TextInput(label=add_error(f"Frame Number ({minn} to {maxn})", err_msg[0]), default=data["use_frame"])
            self.add_item(self.frame)
        elif input_type == 1: # set_colours
            self.colour_1 = discord.ui.TextInput(label=add_error("Colour 1", err_msg[0]), default=data["colour_1"])
            self.colour_2 = discord.ui.TextInput(label=add_error("Colour 2", err_msg[1]), default=data["colour_2"])
            self.colour_3 = discord.ui.TextInput(label=add_error("Colour 3", err_msg[2]), default=data["colour_3"])
            [self.add_item(i) for i in [self.colour_1, self.colour_2, self.colour_3]]
        elif input_type == 2:
            self.animation_seq = discord.ui.TextInput(label=add_error("Animation Sequence (or `none`)", err_msg[0]), default=str(data["animation_seq"]))
            self.animation_speed = discord.ui.TextInput(label=add_error("Animation Speed", err_msg[1]), default=str(data["animation_speed"]))
            [self.add_item(i) for i in [self.animation_seq, self.animation_speed]]
        elif input_type == 3: # other_options
            self.animation_fps = discord.ui.TextInput(label=add_error("Animation FPS", err_msg[0]), default=data["animation_fps"])
            self.output_zip = discord.ui.TextInput(label="Output ZIP (`true` or `false`)", default=str(data["output_zip"]))
            self.crop_transparency = discord.ui.TextInput(label="Crop Transparency (`true` or `false`)", default=str(data["crop_transparency"]))
            [self.add_item(i) for i in [self.animation_fps, self.output_zip, self.crop_transparency]]

    async def on_submit(self, interaction):
        if self.input_type == 0: # set_frame
            err_msg = [None]
            self.data["animated"] = False
            self.data["output_zip"] = False
            async def invalid_number(not_range=False): 
                err_msg[0] = "Out of Range" if not_range else "Invalid Number"
                self.data["use_frame"] = self.frame.value
                await interaction.response.send_message(err_msg[0], ephemeral=True, view=RetryModalView(self, err_msg))
            try:
                f = int(self.frame.value)
            except ValueError:
                return await invalid_number()
            if not (f >= self.frame_range[0] and f <= self.frame_range[1]):
                return await invalid_number(True)
            self.data["use_frame"] = f
        elif self.input_type == 1: # set_colours
            err_msg = [None, None, None]
            hex_fail = False
            for i, item in enumerate(self.children):
                v = item.value.lstrip("#")
                if v == "gay" or v == "chicory":
                    self.data[f"colour_{i+1}"] = item.value
                    continue
                try:
                    int(v, base=16)
                except ValueError:
                    v = "epic hex fail"
                if len(v) != 6: # epic hex falure
                    err_msg[i] = "Invalid Hex"
                    self.data[f"colour_{i+1}"] = item.value
                    hex_fail = True
                else: # epic hex success
                    self.data[f"colour_{i+1}"] = item.value
            if hex_fail:
                return await interaction.response.send_message("Invalid Hex", ephemeral=True, view=RetryModalView(self, err_msg))
        elif self.input_type == 2:
            if self.animation_seq.value.lower() == "none":
                self.data["animation_seq"] = None
            else:
                err_msg = [None, None]
                seq = self.animation_seq.value.split(";")
                if self.data["sprite"] in prop_animations:
                    invalid_anims = [i for i in seq if i not in prop_animations[self.data["sprite"]] and i]
                else:
                    invalid_anims = []
                if len(seq) >= 10:
                    err_msg[0] = "10 Max"
                    self.data["animation_seq"] = self.animation_seq.value
                    self.data["animation_speed"] = self.animation_speed.value
                    return await interaction.response.send_message(f"Too Many Animations (10 max)", ephemeral=True, view=RetryModalView(self, err_msg))
                elif invalid_anims:
                    err_msg[0] = "Invalid"
                    self.data["animation_seq"] = self.animation_seq.value
                    self.data["animation_speed"] = self.animation_speed.value
                    return await interaction.response.send_message(f"Invalid Animation{'s' if (len(invalid_anims) > 1) else ''}: `{'`, `'.join(invalid_anims)}`", ephemeral=True, view=RetryModalView(self, err_msg))
                else:
                    self.data["animation_seq"] = self.animation_seq.value
            try:
                self.data["animation_speed"] = float(self.animation_speed.value)
            except ValueError:
                err_msg[1] = "Invalid Number"
                self.data["animation_speed"] = self.animation_speed.value
                return await interaction.response.send_message("Invalid Number", ephemeral=True, view=RetryModalView(self, err_msg))
        elif self.input_type == 3:
            err_msg = [None]
            try:
                self.data["animation_fps"] = int(self.animation_fps.value)
            except ValueError:
                err_msg[0] = "Invalid Number"
                self.data["animation_fps"] = self.animation_fps.value
                return await interaction.response.send_message("Invalid Number", ephemeral=True, view=RetryModalView(self, err_msg))
            self.data["output_zip"] = self.output_zip.value.lower().strip() == "true" # Default to false on anything else
            self.data["crop_transparency"] = self.crop_transparency.value.lower().strip() != "false" # Default to true on anything else
        out, file, msg, temp = await create_sprite(interaction, **self.data)
        att = [file] if file else []
        if interaction.user.id == self.original_user: # original user
            await msg.delete()
            await self.message.edit(content=out, attachments=att, view=SpriteModificationView(animated=(temp is not None)))
        else:
            await msg.edit(content=out, attachments=att, view=SpriteModificationView(animated=(temp is not None)))
        if file:
            file.close()
        del_temp(temp)

class SpriteModificationView(discord.ui.View):
    def __init__(self, animated, random_sprite=False):
        super().__init__(timeout=None)
        if animated:
            self.animate.label = "Make Image"
            self.animate.emoji = "🖼️"
        if not random_sprite:
            self.remove_item(self.random)

    async def send_modal(self, interaction, type):
        data = await get_data(interaction.message)
        modal = SpriteInputModal(type, data, interaction.message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Make Animated", emoji="📽️", custom_id="spritemod:animate")
    async def animate(self, interaction, button):
        data = await get_data(interaction.message)
        user = data["user"]
        data.pop("user")
        data.pop("random")
        data["animated"] = not data["animated"]
        data["output_zip"] = False
        out, file, msg, temp = await create_sprite(interaction, **data)
        att = [file] if file else []
        if interaction.user.id == user: # original user
            await msg.delete()
            await interaction.message.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        else:
            await msg.edit(content=out, attachments=[file], view=SpriteModificationView(animated=(temp is not None)))
        if file:
            file.close()
        del_temp(temp)

    @discord.ui.button(label="Change Frame", emoji="🎞️", custom_id="spritemod:set_frame")
    async def set_frame(self, interaction, button):
        await self.send_modal(interaction, 0)

    @discord.ui.button(label="Set Colours", emoji="🖌️", custom_id="spritemod:set_colours")
    async def set_colours(self, interaction, button):
        await self.send_modal(interaction, 1)

    @discord.ui.button(label="Animation Options", emoji="🏃", custom_id="spritemod:animation")
    async def animation(self, interaction, button):
        await self.send_modal(interaction, 2)

    @discord.ui.button(label="Other Options", emoji="⚙️", custom_id="spritemod:other_options")
    async def other_options(self, interaction, button):
        await self.send_modal(interaction, 3)

    @discord.ui.button(label="Random", emoji="🔀", custom_id="spritemod:re_random")
    async def random(self, interaction, button):
        sprite = interaction.client.get_cog("SpriteCog")
        data = await get_data(interaction.message)
        animated, colors, palette = data["random"].split(";")
        animated = animated == "1"
        colors = colors == "1"
        for cmd in sprite.walk_app_commands():
            if cmd.name == "random_character":
                await cmd.callback(sprite, interaction, animated, colors, palette)

async def create_sprite(
        interaction: discord.Interaction,
        sprite: str, animated: bool=False, animation_seq: str=None, animation_fps: int=10, animation_speed: int=1,
        crop_transparency: bool=True, use_frame: str=None, output_zip: bool=False,
        colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None,
        random_sprite: str=""
    ):
    await interaction.response.defer()
    sprite = sprite.replace(" ","_")

    colour_3 = colour_3 or colour_1
    
    if isinstance(colour_1, str): # Users COULD put any number of #'s and it'd be a valid colour because of lstrip so to not break anything i'll make sure it's only 1
        colour_1 = "#" + colour_1.lstrip("#")
        if colour_1 == "#gay" or colour_1 == "#chicory": colour_1 = colour_1.lstrip("#")
    if isinstance(colour_2, str):
        colour_2 = "#" + colour_2.lstrip("#")
        if colour_2 == "#gay" or colour_2 == "#chicory": colour_2 = colour_2.lstrip("#")
    if isinstance(colour_3, str):
        colour_3 = "#" + colour_3.lstrip("#")
        if colour_3 == "#gay" or colour_3 == "#chicory": colour_3 = colour_3.lstrip("#")

    if output_zip and not animated:
        animated = True

    if animation_seq:
        animation_fps = None
    else:
        animation_fps = round(animation_fps)
        animation_fps = min(max(animation_fps, 1), 50)

    if (animated and not output_zip) and not gifsicle:
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
    
    anims = None
    delays = None
    if not animation_seq:
        frames = sprite.layer.get_frames()
    else:
        frames = []
        order = []
        delays = []
        if sprite.layer.speed != 1 and animation_speed == 1:
            animation_speed = sprite.layer.speed
        disallowed_anims = [] # For animations with more than 100 frames I disallow using them multiple times
        anims = [i for i in animation_seq.split(";")]
        if len(anims) > 10:
            await interaction.followup.send(content="Too many animations in sequence. Max of 10 is allowed")
            raise errors.PropAnimationError()
        for anim in anims:
            anim = anim.strip()
            if not anim: # blank, likely a trailing ;
                continue
            if name not in prop_animations or anim not in prop_animations[name]:
                if animation_seq == "teehee ;)":
                    await interaction.followup.send(content=f"Invalid animation (`{anim}`). Use `/animations` to check animations or use command autocomplete! teehee ;)")
                else:
                    await interaction.followup.send(content=f"Invalid animation (`{anim}`). Use `/animations` to check animations or use command autocomplete!")
                raise errors.PropAnimationError()
            if anim in disallowed_anims:
                await interaction.followup.send(content=f"Animation `{anim}` has over 100 frames and so cannot be used more than once.")
                raise errors.PropAnimationError()
            animdata = prop_animations[name][anim]["frames"]
            if animdata["end"] - animdata["start"] >= 100:
                disallowed_anims.append(anim)
            add_anim = True
            for frame in range(animdata["start"], animdata["end"]+1):
                if animdata["holds"] != -1 and str(frame) in animdata["holds"]:
                    hold = animdata["holds"][str(frame)]
                    if isinstance(hold, (int, float)):
                        delays.append(hold)
                    elif isinstance(hold, list):
                        delays.append(hold[0]) # does the first hold currently, could add an option to randomize
                else:
                    delays.append(1)
                if add_anim:
                    if frame not in frames or output_zip:
                        frames.append((frame, anim))
                    order.append(frame)
                    add_anim = False
                else:
                    if frame not in frames or output_zip:
                        frames.append(frame)
                    order.append(frame)

    wasanimated = False
    if len(frames) == 1 and animated:
        animated = False
        wasanimated = True
    
    content = "Making Image"
    if animated:
        content += "s (1/2)"
    elif wasanimated:
        content += f" (single frame {'sprite' if not animation_seq else 'anim'}, does not need to be animated)"
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
            if not anims:
                frames = [f]
            else:
                frames = [(f, anims[0])]

    crop = None
    anim = None

    for frame in frames:
        if isinstance(frame, tuple):
            frame, anim = frame
        im = await sprite.layer.load_frame(frame, colour=colour_1)
        for i in sorted(layers[1:]):
            if isinstance(i, Layer):
                layer = i
            else:
                layer = sprite[i]
            if frame in layer.get_frames():
                sproot = layer.root
                layerframe = frame
                if layer.offset:
                    layerframe -= layer.offset
                layernum = layer.num
                col = colour_2 if (layernum % 2 == 0) else colour_3
                im2 = await layer.load_frame(layerframe, anim=anim, colour=col)
                im2n = numpy.array(im2)
                im2n = numpy.where(im2n[:, :, 3] > 0)
                if (im2n[0].size == 0 and im2n[1].size == 0) and anim != None and name != "Logo_alt": # Image fully transparent and there is an animation
                    im2 = await layer.load_frame(layerframe, colour=col) # use regular image instead of one from anim
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
                if crop[0] == crop[2]:
                    crop[2] += 1
                if crop[1] == crop[3]:
                    crop[3] += 1
            except ValueError:
                pass # Blank Image
        if animated:
            if anims and not output_zip: # Animation sequence, the same image could happen multiple times, so we save it once and put it in the right order later.:
                im.save(temp / f"{frame:03}.png")
            else:
                im.save(temp / f"{frameN:03}.png")
            frameN += 1
        else:
            if crop_transparency and crop:
                ims = im.crop(box=crop)
            else:
                ims = im
            break

    def rgb_to_hex(rgb):
        if not isinstance(rgb, (list, tuple)):
            print(rgb)
            raise errors.ColourError()
        r,g,b = rgb
        return "#{:02x}{:02x}{:02x}".format(r,g,b)

    data = {
        "user": interaction.user.id,
        "sprite": name, "animated": animated, "animation_seq": animation_seq, "animation_fps": animation_fps or 10, "animation_speed": animation_speed,
        "crop_transparency": crop_transparency, "use_frame": use_frame, "output_zip": output_zip,
        "colour_1": colour_1 if isinstance(colour_1, str) else rgb_to_hex(colour_1), "colour_2": colour_2 if isinstance(colour_2, str) else rgb_to_hex(colour_2), "colour_3": colour_3 if isinstance(colour_3, str) else rgb_to_hex(colour_3),
        "random": random_sprite
    }

    for i in default_data.keys():
        if data[i] == default_data[i]:
            data.pop(i)

    data = json.dumps(data, separators=(",",":")) # This is probably not very efficient but is cool reference
    data = zlib.compress(data.encode("utf-8"))
    data = b64encode(data).decode("utf-8")
    data = f"[:](http://ignorethis/${data}$)"

    if not animated:
        imbyte = BytesIO()
        ims.save(imbyte, "PNG")
        imbyte.seek(0)
        if isinstance(frames[0], tuple):
            frames[0] = frames[0][0]
        out = f"`{name}` frame `{frames[0]}`{data}\n"
        if animation_seq:
            out += f"Animation: `{anims[0]}`\n"
        if wasanimated:
            out += f"(Single frame {'sprite' if not animation_seq else 'anim'}, animation not required)"
        file = discord.File(imbyte, f"{name}.png")
        return out, file, msg, None

    giferror = False

    if animated and not output_zip:
        await msg.edit(content="Combining Images (2/2)")
        addcrop = f"-crop {crop[2]-crop[0]}x{crop[3]-crop[1]}+{crop[0]}+{crop[1]} +repage " if crop_transparency else ""
        im_list = f"{temp}/*.png "
        delay_fps = f"-delay 1x{animation_fps} "
        if delays:
            delay_fps = ""
            im_list = ""
            for i, v in enumerate(order):
                path = temp / f"{v:03}.png"
                d = delays[i]
                # if d == 1:
                #     d = f"{animation_speed}x60" # hold being 1 means 1 frame THIS IS WRONG?
                # else:
                d = round(d * 7.5 / 60 * 100 / animation_speed) # hold * 7.5 is how many frames it should hold (also imagemagick uses centi seconds for some reason)
                im_list += f"-delay {d} {path} "
        print(f"{imagemagick} -loop 0 -dispose Background {delay_fps}{im_list}{addcrop} {temp / 'out.gif'}")
        process = await asyncio.create_subprocess_shell(
            f"{imagemagick} -loop 0 -dispose Background {delay_fps}{im_list}{addcrop} {temp / 'out.gif'}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0: # Error
            print(f"GIF CONVERSION ERROR: {stderr.decode()}")
            if anims: # Since all frames aren't done in anim seqs sending a zip right now would make it not be in the order they requested.
                return f"{data}GIF Conversion Failed. Set Output Zip in Other Options to true to send a zip with PNGs.", None, msg, temp
            output_zip = True
            giferror = True
        else:
            if anims:
                out = f"`{name}`{data}\n"
                out += f"Animation Seq: `{'`, `'.join(anims)}`"
            else:
                out = f"`{name}` at {animation_fps} fps{data}\n"
            file = discord.File(temp / "out.gif", f"{name}.gif")
            return out, file, msg, temp

    if animated and output_zip:
        await msg.edit(content=f"Zipping PNGs"+ (", Gif Conversion Failed" if giferror else "") +" (2/2)")
        f = BytesIO()
        with zipfile.ZipFile(f, "x") as zipf:
            for i in temp.glob("*.png"):
                zipf.write(i, i.relative_to(temp))
        f.seek(0)
        file = discord.File(f, f"{name}.zip")
        out = f"`{name}`{data}"
        return out, file, msg, temp

class SpriteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name="Get Sprite Info", callback=self.sprite_info, extras={"ephemeral": True})
        bot.tree.add_command(self.ctx_menu)
        modview = SpriteModificationView(1, True)
        if not self.bot.SpriteModificationView:
            self.bot.SpriteModificationView = modview
            self.bot.add_view(self.bot.SpriteModificationView)
        else:
            self.bot.SpriteModificationView = modview

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @app_commands.command(description="Show a sprite.")
    @app_commands.describe(
        sprite="The sprite to show", animated="If True, sends an animated gif", animation_seq="Sequence of animations, separated by a ;.",
        animation_fps="If animated and animation_seq is NOT used, sets the FPS of the animation (max 50)", animation_speed="If animated and animation_seq is used, sets the speed to play the animation. (Best <=4)",
        crop_transparency="Removes any blank area around the image", use_frame="If not animated, choose a frame of the sprite to send (starts at 0)", output_zip="Outputs animation as a zip of PNGs for high quality."
    )
    @app_commands.autocomplete(sprite=autocomplete.sprite, animation_seq=autocomplete.animation_seq)
    async def sprite(
            self, interaction: discord.Interaction,
            sprite: str, animated: bool=False, animation_seq: str=None, animation_fps: int=10, animation_speed: int=1,
            crop_transparency: bool=True, use_frame: str=None, output_zip: bool=False,
            colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None
        ):
        out, file, msg, temp = await create_sprite(
            interaction,
            sprite, animated, animation_seq, animation_fps, animation_speed,
            crop_transparency, use_frame, output_zip,
            colour_1, colour_2, colour_3
        )
        att = [file] if file else []
        await msg.edit(content=out, attachments=att, view=SpriteModificationView(animated=(temp is not None))) # idk if i wanna add create_sprite returning if it is animated (it can change with 1 frame sprites) but there being a temp is a 100% way to know
        if file:
            file.close()
        del_temp(temp)

    # Get Sprite Info Context Menu
    async def sprite_info(self, interaction, message: discord.Message):
        try:
            data = await get_data(message)
        except ValueError:
            return await interaction.response.send_message("Sprite not found in the message.", ephemeral=True)
        embed = discord.Embed(title="Sprite Info")
        for key in ["user", "sprite", "use_frame", "output_zip", "animated", "animation_name", "animation_seq", "animation_speed", "animation_fps", "colour_1", "colour_2", "colour_3"]:
            if key not in data and key == "animation_name":
                continue
            value = data[key]
            if key == "user":
                value = f"<@{value}>"
            else:
                value = f"`{value}`"
            embed.add_field(name=to_titlecase(key.replace("_", " ")), value=value, inline=(key != "user"))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Gets a random character.")
    @app_commands.autocomplete(use_palette=autocomplete.random_palette)
    async def random_character(self, interaction, animated: bool=False, colors: bool=True, use_palette: str="None"):
        sprite = random.choice(characters)
        if sprite in characters_dupes:
            sprite = random.choice(characters_dupes[sprite])
        if colors:
            if use_palette.lower() != "none": # Single palette limited
                if use_palette.lower() != "random": # Specified palette
                    palette = to_titlecase(use_palette)

                    if palette in paletteAliases:
                        chosen = paletteAliases[palette]
                    else:
                        return await interaction.response.send("Incorrect palette.")
                else:
                    chosen = random.choice(randomablePalettes)
                cols = palettes[chosen]
            else: # Not single palette limited
                cols = all_colours
            colour_1 = tuple(random.choice(cols))
            colour_2 = tuple(random.choice(cols))
        else:
            colour_1 = "#ffffff"
            colour_2 = "#ffffff"
        out, file, msg, temp = await create_sprite(
            interaction,
            sprite, animated, None, 10, 1,
            True, None, False,
            colour_1, colour_2, colour_1,
            f"{int(animated)};{int(colors)};{use_palette}"
        )
        att = [file] if file else []
        if colors and use_palette.lower() != "none":
            out += f"{'Random ' if use_palette.lower() == 'random' else ''}Palette: `{chosen}`"
        await msg.edit(content=out, attachments=att, view=SpriteModificationView(animated=(temp is not None), random_sprite=True))
        if file:
            file.close()
        del_temp(temp)