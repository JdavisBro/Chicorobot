import json
import random
import sys
import shutil
import inspect
import math
import tempfile
import textwrap
import zipfile
import zlib
from base64 import b64decode, b64encode
from io import BytesIO, StringIO
from pathlib import Path
from contextlib import redirect_stdout

import asyncio
import discord
from discord import app_commands
from PIL import Image, ImageChops#, ImageDraw, ImageFont
import numpy
from typing import Union

import errors
from sprites import *
from assets import *

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

# Check for imagemagick
imagemagick: Union[Path, str, None] = None
if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
    imagemagick = shutil.which("magick")
else:
    imagemagick = shutil.which("convert")
if not imagemagick:
    imagemagick = Path("imagemagick/convert.exe")
    if not imagemagick.exists():
        imagemagick = None

# Util Funcs
def to_titlecase(string):
    if "-" in string:
        return "-".join([word[0].upper() + word[1:].lower() for word in string.split("-")]) # Half-Moons
    else:
        return " ".join([word[0].upper() + word[1:].lower() for word in string.split(" ")])

# Discord Client
class Chicorobot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.previous_exec = None
        self.ownerid = 0

    async def setup_hook(self):
        #guild = discord.Object(473976215301128193) # msmg
        guild = discord.Object(947898290735833128)

        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)

        self.add_view(SpriteModificationView(animated=False))
        
        appinfo = await client.application_info()
        client.ownerid = appinfo.owner.id

client = Chicorobot()
tree = app_commands.CommandTree(client)

# Discord Events and Error Handling
@client.event
async def on_ready():
    print("LOGGED IN!")

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

# Commands
# Function that creates and sends dogs, used by dog and random_dog
async def make_dog(interaction: discord.Interaction,
        expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
        body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
        custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
        extra_text: str=""
    ):
    await interaction.response.defer(thinking=True)

    clothes = to_titlecase(clothes)
    hat = to_titlecase(hat)
    hat2 = to_titlecase(hat2)

    expression = expression.lower()

    base_size = (750, 750)

    # -- Animation _B -- #
    im = await sprites["Dog_idle_B"].layer.load_frame(0, resize=base_size, colour=body_col)

    if clothes != "Custom":
        # -- Clothing -- #
        if not sprites.body.is_frame(clothes):
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{clothes}` is not a clothing!")
            return
        im2 = await sprites.body.load_frame(clothes, resize=base_size, colour=clothes_col) # Clothes
        im.alpha_composite(im2)
    else:
        # -- Custom Clothing -- #
        if not custom_clothes:
            await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply custom clothes!")
            return
        im2 = BytesIO()
        await custom_clothes.save(im2)
        im2 = Image.open(im2, formats=["PNG"])
        im3 = Image.new("RGBA", im.size, (0,0,0,0))
        im3.paste(im2,box=(220,433),mask=im2)
        im3 = await colour_image(im3, clothes_col)
        im.alpha_composite(im3)

    # -- Clothing _0 -- #
    if sprites.body2.is_frame(clothes+"_0"):
        im2 = await sprites.body2.load_frame(clothes + "_0", resize=base_size, colour=hat_col)
        im.alpha_composite(im2)

    # -- Animation _A -- #
    im2 = await sprites["Dog_idle_A"].layer.load_frame(0, resize=base_size, colour=body_col)
    im.alpha_composite(im2)

    # -- Clothing _1 -- #
    if sprites.body2.is_frame(clothes+"_1"):
        im2 = await sprites.body2.load_frame(clothes+"_1", resize=base_size, colour=hat_col)
        im.alpha_composite(im2)
    
    # -- Neck Hats -- #
    for h in [hat,hat2]:
        if h in extraHats:
            im2 = await sprites.body2.load_frame(h+"_1", resize=base_size, colour=hat_col)
            im.alpha_composite(im2)

    # -- Expression -- #
    if expression != "normal":
        if not sprites.expression.is_frame(expression):
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{expression}` is not an expression!")
            return
        im2 = await sprites.expression.load_frame(expression, resize=base_size, colour=body_col)
    else:
        im3 = await sprites.head.load_frame(0, colour=body_col)
        im2 = Image.new("RGBA", base_size)
        im2.paste(im3, box=(150, 50))
    im.alpha_composite(im2)    

    # -- Clothing _2 -- #
    if sprites.body2.is_frame(clothes+"_2"):
        im2 = await sprites.body2.load_frame(clothes+"_2", resize=base_size, colour=clothes_col)
        im.alpha_composite(im2)
    
    # -- Hats _1 -- #
    for h in [hat,hat2]:
        if sprites.hat.is_frame(h+"_1"): # Behind hair part of hat (only used for horns)
            im2 = await sprites.hat.load_frame(h+"_1", resize=base_size, colour=hat_col)
            im.alpha_composite(im2)

    # -- Hair -- #
    if all([h in hairHats for h in [hat,hat2]]): # Neither hat doesn't show hair
        if not sprites.hair.is_frame(hair):
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{hair}` is not a hair!")
            return
        im2 = await sprites.hair.load_frame(hair, resize=base_size, colour=body_col)
        im.alpha_composite(im2)

    # -- Hat -- #
    async def do_hat():
        for h in [hat, hat2]:
            if h == "None" or h in extraHats:
                continue
            if h != "Custom":
                im2 = await sprites.hat.load_frame(h, resize=base_size, colour=hat_col)
                im.alpha_composite(im2)
            else:
                if not custom_hat:
                    await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply a custom hat!")
                    return
                im2 = BytesIO()
                await custom_hat.save(im2)
                im2 = Image.open(im2, formats=["PNG"])
                im3 = Image.new("RGBA", im.size, (0,0,0,0))
                im3.paste(im2,box=(129,45),mask=im2)
                im.alpha_composite(await colour_image(im3, hat_col))

    async def do_ear():
        im2 = await sprites["Dog_idle_ear"].layer.load_frame(0, resize=base_size, colour=body_col)
        im.alpha_composite(im2)

    for h in [hat, hat2]:
        if h == "None" or h == "Custom" or h in extraHats:
            continue
        if not sprites.hat.is_frame(h):
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{h}` is not a hat!")
            return

    if any([h in hatOverEar for h in [hat,hat2]]):
        await do_ear()
        await do_hat()
    else:
        await do_hat()
        await do_ear()

    imbyte = BytesIO()
    im.save(imbyte, "PNG")
    imbyte.seek(0)
    file = discord.File(imbyte, "dog.png")
    await interaction.followup.send(content=f"Dog:\n`/dog expression:{expression} clothes:{clothes} hat:{hat} hair:{hair} hat2:{hat2} body_col:{('#%02x%02x%02x' % body_col) if isinstance(body_col, tuple) else body_col} clothes_col:{('#%02x%02x%02x' % clothes_col) if isinstance(clothes_col, tuple) else clothes_col} hat_col:{('#%02x%02x%02x' % hat_col) if isinstance(hat_col, tuple) else hat_col}`{extra_text}", file=file)

@tree.command(name="random_dog", description="Make a random dog!")
@app_commands.describe(use_palettes="Only use colours from the game. Default: True", limit_to_one_palette="Choose one palette from the game and use colours from it. Default: False", palette="Specify palette to be used with limit_to_one_palette. Default: Random" , add_hat2="Add a random hat2. Default: False")
async def random_dog(interaction: discord.Interaction, use_palettes: bool=True, limit_to_one_palette: bool=False, palette: str=None, add_hat2: bool=False):
    chosen = None
    if use_palettes:
        if limit_to_one_palette: # Single palette limited
            if palette != None and palette.lower() != "random": # Specified palette
                palette = to_titlecase(palette)

                if palette in paletteAliases:
                    chosen = paletteAliases[palette]
                else:
                    return await interaction.response.send("Incorrect palette.")
            else:
                chosen = random.choice(randomablePalettes)
            cols = palettes[chosen]
        else: # Not single palette limited
            cols = all_colours
        colone = tuple(random.choice(cols))
        coltwo = tuple(random.choice(cols))
        colthree = tuple(random.choice(cols))
    else:
        colone = discord.Colour.random()
        coltwo = discord.Colour.random()
        colthree = discord.Colour.random()
    await make_dog(
        interaction,
        random.choice(sprites["Dog_expression"].layer.get_frames()),
        random.choice(sprites["Dog_body"].layer.get_frames()),
        random.choice([i for i in sprites["Dog_hat"].layer.get_frames() if i != "Horns_1"] + ["None"] + extraHats),
        random.choice(sprites["Dog_hair"].layer.get_frames()),
        "None" if not add_hat2 else random.choice(sprites["Dog_hat"].layer.get_frames() + ["None"] + extraHats),
        colone,
        coltwo,
        colthree,
        extra_text="" if not limit_to_one_palette else f"\nPalette: {chosen}"
    )

@tree.command(name="dog", description="Make a Dog!")
async def dog(interaction: discord.Interaction,
        expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
        body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
        custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None
    ):
    await make_dog(interaction, expression, clothes, hat, hair, hat2, body_col, clothes_col, hat_col, custom_clothes, custom_hat)

# dog autocompletes
@dog.autocomplete("clothes")
async def clothes_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted(sprites.body.get_frames() + ["Custom"])
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("expression")
async def expression_autocomplete(interaction: discord.Interaction, current: str):
    ls = ["normal"] + sorted(sprites.expression.get_frames())
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("hat")
@dog.autocomplete("hat2")
async def hat_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted(sprites.hat.get_frames() + ["None", "Custom"] + extraHats)
    if "Horns_1" in ls:
        ls.remove("Horns_1")
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("hair")
async def hair_autocomplete(interaction: discord.Interaction, current:str):
    ls = sorted(sprites.hair.get_frames())
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

# Sprite command
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

async def create_sprite(
        interaction: discord.Interaction,
        sprite: str, animated: bool=False, animation_name: str=None, animation_fps: int=10,
        crop_transparency: bool=True, use_frame: str=None, output_zip: bool=False,
        colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None
    ):
    await interaction.response.defer()
    sprite = sprite.replace(" ","_")

    colour_3 = colour_3 or colour_1

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
            return
        elif not namestr and not sprite.layer.frames: # They gave us a number but we only have string frames
            await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
            return
        if namestr:
            if f not in sprite.layer.get_frames():
                await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
                return
            frames = [f]
        else:
            if f >= len(frames):
                await msg.edit(content="Invalid frame. Use `/frames` to check available frames!")
                return
            frames = [f]

    crop = None

    for frame in frames:
        f = frame
        filePath = Path(sprite.layer.root + f"{str(frame)}.png")
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
            im.save(temp / f"{frameN:03}.png")
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
        out = f"{name} frame `{f}`{' (one frame sprite, animation not required)' if wasanimated else ''}:{data}\n"
        file = discord.File(imbyte, f"{name}..png")
        return out, file, msg, None

    giferror = False

    if animated and not output_zip:
        await msg.edit(content="Converting PNGs to GIF (2/2)")
        addcrop = f"-crop {crop[2]-crop[0]}x{crop[3]-crop[1]}+{crop[0]}+{crop[1]} +repage " if crop_transparency else ""
        process = await asyncio.create_subprocess_shell(
            f"{imagemagick} -delay 1x{animation_fps} -loop 0 -dispose Background {addcrop}{temp / '*.png'} {temp / 'out.gif'}", # imagemagick is the only good way I've found of creating a GIF in python without it being horrible quality or not maintaining transparency.
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if process.returncode != 0: # Error
            print(f"GIF CONVERSION ERROR: {await process.stdout.read()}")
            giferror = True
        else:
            out = f"{name} at {animation_fps} fps:{data}\n"
            file = discord.File(temp / "out.gif", f"{name}.gif")
            return out, file, msg, temp

    if animated and (output_zip or giferror):
        await msg.edit(content=f"{'GIF Conversion failed, ' if giferror else ''}Zipping PNGs (2/2)")
        f = BytesIO()
        with zipfile.ZipFile(f, "x") as zipf:
            for i in temp.iterdir():
                zipf.write(i, i.relative_to(temp))
        f.seek(0)
        file = discord.File(f, f"{name}.zip")
        out = f"{name}:{data}" if not giferror else f"{name} (Zip, GIF conversion failed):{data}\n"
        return out, file, msg, temp

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
        self.original_user = data["user"]
        self.data.pop("user")
        if input_type == 0: # set_frame
            self.frame = discord.ui.TextInput(label="Frame Number", default=data["use_frame"])
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
            try:
                self.data["use_frame"] = int(self.frame.value)
            except ValueError:
                self.frame.label = "Frame Number - Invalid Number"
                return await interaction.response.send_message("Invalid Number", ephemeral=True, view=RetryModalView(self))
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

@tree.command(description="Show a sprite.")
@app_commands.describe(
    sprite="The sprite to show", animated="If True, sends an animated gif", animation_name="Name of the animation to use, get a list of them for a sprite using /animations.", animation_fps="If animated. Sets the FPS of the animation (max 50)",
    crop_transparency="Removes any blank area around the image", use_frame="If not animated, choose a frame of the sprite to send (starts at 0)", output_zip="Outputs animation as a zip of PNGs for high quality."
)
async def sprite(
        interaction: discord.Interaction,
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

@tree.command(description="Lists animations for a specific sprite")
async def animations(interaction: discord.Interaction, sprite: str):
    anims = []
    for layer in sprites[sprite].get_layers():
        if sprites[sprite][layer].anim_root:
            anims += list(sprites[sprite][layer].anim_root)
    await interaction.response.send_message(content=f"{sprite} animations: `{'`, `'.join(anims)}`")

@animations.autocomplete("sprite")
async def animations_sprite_autocomplete(interaction: discord.Interaction, current: str):
    lst = []
    for sprite in sprites.sprites():
        if current.lower() not in sprite.lower():
            continue
        if [layer for layer in sprites[sprite].get_layers() if sprites[sprite][layer].anim_root]:
            lst.append(sprite)
            continue
    return [app_commands.Choice(name=i, value=i) for i in lst]

@tree.command(description="Lists frames for a specific sprite")
async def frames(interaction: discord.Interaction, sprite: str):
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

@sprite.autocomplete("sprite")
@frames.autocomplete("sprite")
async def sprite_autocomplete(interaction: discord.Interaction, current: str):
    lst = sorted(list(sprites.sprites()) + ["Random"])
    return [app_commands.Choice(name=i, value=i) for i in lst if current.lower() in i.lower()][:25]

@tree.command(description="Get a palette from the game!")
@app_commands.describe(
    area_name="Name of an area from the game. Not required if code_name specified.",
    code_name="Name of a palette in the games code. Not required if area_name specified."
)
async def palette(interaction: discord.Interaction, area_name: str=None, code_name: str="Random"):
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

# Palette autocompletes
@palette.autocomplete("area_name")
@random_dog.autocomplete("palette")
async def area_name_autocomplete(interaction: discord.Interaction, current: str):
    lst = [i for i in sorted(
        [i for i in paletteAliases.keys()] + ["Random"]
    ) if current in i][:25]
    return [app_commands.Choice(name=i, value=i) for i in lst]

@palette.autocomplete("code_name")
async def code_name_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=i, value=i) for i in sorted(
        [i for i in palettes.keys()] + ["random"]
    ) if current in i][:25]

# Other simple/owner commands
@tree.command(description="Send a picture of hair to number.")
async def hair(interaction: discord.Interaction):
    await interaction.response.send_message(content="https://media.discordapp.net/attachments/967965561361428490/1004109210151301120/unknown.png", ephemeral=True)

# Checks if user is owner
def is_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == client.ownerid
    return app_commands.check(predicate)

@tree.command(description="Death.")
@is_owner()
async def die(interaction: discord.Interaction):
    await interaction.response.send_message(content="I hath been slayn.")
    await client.close()

# Modal for the exec command input and processing.
class ExecModal(discord.ui.Modal, title="Execute Code!"):
    code = discord.ui.TextInput(label="Code!", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Reworked from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L216-L261

        env = {
            "client": client,
            "interaction": interaction,
            "guild": interaction.guild,
            "channel": interaction.channel,
            "user": interaction.user,
            "_": client.previous_exec
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
            out = stdout.getvalue()
            if out:
                await interaction.followup.send(f"```py\n{out}\n```", ephemeral=True)
            if value:
                client.previous_exec = value
                await interaction.followup.send(value)

# Just sends the exec modal
@tree.command(name="exec", description="HACKING CODING.")
@is_owner()
async def execute(interaction: discord.Interaction):
    await interaction.response.send_modal(ExecModal())

# run.
client.run(TOKEN)
