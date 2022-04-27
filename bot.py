import json
import random
import sys
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

import asyncio
import discord
from discord import app_commands
from PIL import Image, ImageChops#, ImageDraw, ImageFont
import numpy

with Path("TOKEN.txt").open("r") as f:
    TOKEN = f.readline().rstrip()

if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
    imagemagick = shutil.which("magick")
else:
    imagemagick = shutil.which("convert")
if not imagemagick:
    imagemagick = Path("imagemagick/convert.exe")
    if not imagemagick.exists():
        imagemagick = False

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# TEST_GUILD = discord.Object(473976215301128193) # msmg
TEST_GUILD = discord.Object(947898290735833128) # gay baby jail

with Path("palettes.json").open("r") as f:
    palettes = json.load(f)

all_colours = []
for v in palettes.values():
    all_colours += v
all_colours += [[242, 0, 131],[217, 199, 190]] # Pickle and dust!

randomablePalettes = [i for i in palettes.keys() if i not in ["boss1", "boss2", "town_spooky", "town_spooky2", "town_postgame"]]

with Path("sprites.json").open("r") as f:
    sprites = json.load(f)

spr = Path("Export_Sprites/")

hairHats = (
    "Aviators",
    "Beak",
    "Beard",
    "Big Shades",
    "Bow",
    "Clown",
    "Eyepatch",
    "Flower",
    "Goggles",
    "Half-Moons",
    "Headband",
    "Horns",
    "Kerchief",
    "Line Shades",
    "Mask",
    "Monocle",
    "None",
    "Pointish Glasses",
    "Rim Shades",
    "Round Glasses",
    "Scarf",
    "Shades",
    "Shawl",
    "Sparkles",
    "Spike",
    "Square Glases",
    "Stache",
    "Stormy",
    "Studs",
    "Superstar",
    "Tiara",
    "Tinted Shades"
)

hatOverEar = (
    "Ahoy",
    "Big Fungus",
    "Custom",
    "Earmuffs",
    "Headphones",
    "Howdy",
    "Rex Head",
    "Spellcaster",
    "Strawhat",
    "Sunhat",
    "Top Hat"
)

extraHats = [
    "Shawl",
    "Spike",
    "Studs",
    "Kerchief",
    "Scarf"
]

class ColourError(Exception):
    pass

@client.event
async def on_ready():
    await tree.sync(guild=TEST_GUILD)
    
    print("LOGGED IN!")

@tree.error
async def command_error(interaction: discord.Interaction, error):
    error = getattr(error, "original", error)
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("<:Pizza_Angry:967482622194372650> You're not allowed to do that.", ephemeral=True)
        return
    elif isinstance(error, ColourError):
        await interaction.followup.send("You inputted a colour wrong!")
    if not interaction.response.is_done():
        await interaction.response.send_message("<:Pizza_Depressaroli:967482279670718474> Something went wrong.")
    else:
        await interaction.followup.send("<:Pizza_Depressaroli:967482279670718474> Something went wrong.")
    raise error

def clamp(value, min, max):
    return min if value <= min else max if value >= max else value

def to_titlecase(string):
    return " ".join([word[0].upper() + word[1:].lower() for word in string.split(" ")])

def get_location(layer, frame):
    if isinstance(frame, str):
        return spr / f"{layer['root']}{layer['named_frames'][frame]}.png"
    return spr / f"{layer['root']}{layer['frames'][frame]}.png"

async def colour_image(im: Image, colour):
    if not isinstance(colour, tuple):
        colour = colour.lstrip("#")
        if colour == "ffffff":
            return im
        try:
            colour = tuple([int(colour[i:i+2], 16) for i in (0, 2, 4)] + [255])
        except ValueError:
            raise ColourError()
    else:
        colour = tuple(list(colour) + [255])
    return ImageChops.multiply( im, Image.new("RGBA", im.size, colour))

async def make_dog(interaction: discord.Interaction,
        expression: str, clothes: str, hat: str, hair: str="00", hat2: str="None",
        body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
        custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
        extra_text: str=""
    ):
    await interaction.response.defer(thinking=True)

    clothes = to_titlecase(clothes)
    
    hat = to_titlecase(hat)
    hat2 = to_titlecase(hat2)

    expression = expression.lower()

    idleFrame = 0

    im = await colour_image(Image.open(get_location(sprites['Dog_idle_B']['1'], idleFrame)).resize((750, 750)), body_col)

    if clothes != "Custom":
        if not clothes in sprites["Dog_body"]["1"]["named_frames"]:
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{clothes}` is not a clothing!")
            return
        im2 = Image.open(get_location(sprites['Dog_body']['1'], clothes)).resize((750, 750)) # Clothes
        im.alpha_composite(await colour_image(im2, clothes_col))
    else:
        if not custom_clothes:
            await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply custom clothes!")
            return
        im2 = BytesIO()
        await custom_clothes.save(im2)
        im2 = Image.open(im2, formats=["PNG"])
        im3 = Image.new("RGBA", im.size, (0,0,0,0))
        im3.paste(im2,box=(220,433),mask=im2)
        im.alpha_composite(await colour_image(im3, clothes_col))

    if clothes+"_0" in sprites["Dog_body2"]["1"]["named_frames"]:
        im.alpha_composite(await colour_image(Image.open(get_location(sprites['Dog_body2']['1'], clothes+"_0")), hat_col))

    im2 = Image.open(get_location(sprites['Dog_idle_A']['1'], idleFrame)).resize((750, 750)) # Arm
    im.alpha_composite(await colour_image(im2, body_col))

    if clothes+"_1" in sprites["Dog_body2"]["1"]["named_frames"]:
        im.alpha_composite(await colour_image(Image.open(get_location(sprites['Dog_body2']['1'], clothes+"_1")), hat_col))
    
    for h in [hat,hat2]:
        if h in extraHats:
            im.alpha_composite(await colour_image(Image.open(get_location(sprites['Dog_body2']['1'], h+"_1")), hat_col))

    if not expression in sprites["Dog_expression"]["1"]["named_frames"]:
        await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{expression}` is not an expression!")
        return
    im2 = Image.open(get_location(sprites["Dog_expression"]["1"], expression)).resize((750, 750)) # Face
    im.alpha_composite(await colour_image(im2, body_col))    

    if clothes+"_2" in sprites["Dog_body2"]["1"]["named_frames"]:
        im.alpha_composite( await colour_image( Image.open(get_location(sprites['Dog_body2']['1'], clothes+"_2")), clothes_col ) )

    for h in [hat,hat2]:
        if h+"_1" in sprites["Dog_hat"]["1"]["named_frames"]: # Behind hair part of hat (only used for horns)
            im.alpha_composite( await colour_image( Image.open(get_location(sprites['Dog_hat']['1'], h+"_1")), hat_col ) )

    if all([h in hairHats for h in [hat,hat2]]): # Hat shows hair
        if not hair in sprites["Dog_hair"]["1"]["named_frames"]:
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{hair}` is not a hair!")
            return
        im.alpha_composite( await colour_image(Image.open(get_location(sprites["Dog_hair"]["1"], hair)).resize((750, 750)), body_col ) )

    async def do_hat():
        for h in [hat, hat2]:
            if h == "None" or h in extraHats:
                continue
            if h != "Custom":
                im2 = Image.open(get_location(sprites["Dog_hat"]["1"], h)).resize((750, 750)) # Hat
                im.alpha_composite( await colour_image(im2, hat_col))
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
        im2 = Image.open(get_location(sprites["Dog_idle_ear"]["1"], idleFrame)).resize((750, 750)) # Ear
        im.alpha_composite(await colour_image(im2, body_col))

    for h in [hat, hat2]:
        if h == "None" or h == "Custom" or h in extraHats:
            continue
        if h not in sprites["Dog_hat"]["1"]["named_frames"]:
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

@tree.command(guild=TEST_GUILD, name="random_dog", description="Make a random dog!")
@app_commands.describe(use_palettes="Only use colours from the game.", limit_to_one_palette="Choose one palette from the game and use colours from it.", add_hat2="Add a random hat2")
async def random_dog(interaction: discord.Interaction, use_palettes: bool=True, limit_to_one_palette: bool=False, add_hat2: bool=False):
    chosen = None
    if use_palettes:
        if limit_to_one_palette:
            chosen = random.choice(randomablePalettes)
        cols = all_colours if not limit_to_one_palette else palettes[chosen]
        colone = tuple(random.choice(cols))
        coltwo = tuple(random.choice(cols))
        colthree = tuple(random.choice(cols))
    else:
        colone = discord.Colour.random()
        coltwo = discord.Colour.random()
        colthree = discord.Colour.random()
    await make_dog(
        interaction,
        random.choice(list(sprites["Dog_expression"]["1"]["named_frames"].keys())),
        random.choice(list(sprites["Dog_body"]["1"]["named_frames"].keys())),
        random.choice([i for i in sprites["Dog_hat"]["1"]["named_frames"].keys() if i != "Horns_1"] + ["None"] + extraHats),
        random.choice(list(sprites["Dog_hair"]["1"]["named_frames"].keys())),
        "None" if not add_hat2 else random.choice(list(sprites["Dog_hat"]["1"]["named_frames"].keys()) + ["None"] + extraHats),
        colone,
        coltwo,
        colthree,
        extra_text="" if not limit_to_one_palette else f"\nPalette: {chosen}"
    )

@tree.command(guild=TEST_GUILD, name="dog", description="Make a Dog!")
async def dog(interaction: discord.Interaction,
        expression: str, clothes: str, hat: str, hair: str="00", hat2: str="None",
        body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
        custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None
    ):
    await make_dog(interaction, expression, clothes, hat, hair, hat2, body_col, clothes_col, hat_col, custom_clothes, custom_hat)

@dog.autocomplete("clothes")
async def clothes_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted(list(sprites["Dog_body"]["1"]["named_frames"].keys()) + ["Custom"])
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("expression")
async def expression_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted(list(sprites["Dog_expression"]["1"]["named_frames"].keys()))
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("hat")
@dog.autocomplete("hat2")
async def hat_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted(list(sprites["Dog_hat"]["1"]["named_frames"].keys()) + ["None", "Custom"] + extraHats)
    if "Horns_1" in ls:
        ls.remove("Horns_1")
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("hair")
async def hair_autocomplete(interaction: discord.Interaction, current:str):
    ls = sorted(list(sprites["Dog_hair"]["1"]["named_frames"].keys()))
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]


@tree.command(guild=TEST_GUILD, description="Show a sprite.")
@app_commands.describe(
    sprite="The sprite to show", animated="If True, sends an animated gif", animation_name="Name of the animation to use, get a list of them for a sprite using /animations.", animation_fps="If animated. Sets the FPS of the animation",
    crop_transparency="Removes any blank area around the image", use_frame="If not animated, choose a frame of the sprite to send (starts at 1)",
)
async def sprite(interaction: discord.Interaction,
        sprite: str, animated: bool=False, animation_name: str=None, animation_fps: int=10,
        crop_transparency: bool=True, use_frame: str=None,
        colour_1: str="#ffffff", colour_2: str="#ffffff", colour_3: str=None
    ):
    await interaction.response.defer(thinking=True)
    sprite = sprite.replace(" ","_")

    colour_3 = colour_3 or colour_1

    try:
        animation_fps = round(animation_fps)
        if animation_fps < 1:
            animation_fps = 1
    except ValueError:
        await interaction.followup.send("FPS incorrect.")
        return

    if animated and not imagemagick:
        await interaction.followup.send(content="Animated sprites are unavailable, making non animated version.")
        animated = False
    
    if sprite.lower() == "random":
        sprite = random.choice(list(sprites.keys()))
    
    ims = None
    if sprite not in sprites:
        sprite = to_titlecase(sprite)
        if sprite not in sprites:
            await interaction.followup.send(content="Incorrect Sprite")
            return
    name = sprite
    sprite = sprites[name]

    layers = [k for k in sorted(sprite.keys())]
    
    if name.endswith("_A"):
        sproot = "_".join(name.split("_")[:-1]) + "_"
        layers += [sprites[i]["1"] for i in [sproot+"B",sproot+"ear"]]
    
    frameN = 0
    if animated:
        temp = tempfile.mkdtemp()
        temp = Path(temp)
        print(f"Making temp: {str(temp)}")
    
    msg = await interaction.followup.send(content="Making Image" + ("s and saving to PNG (1/2)" if animated else ""))

    crop = None

    if use_frame:
        frames = sprite[layers[0]]["frames"] or sprite[layers[0]]["named_frames"]
        try:
            f = int(use_frame) - 1
            namestr = False
        except ValueError:
            namestr = True
        if namestr:
            if not f in frames:
                await msg.edit("Invalid frame. Use `/frames` to check available frames!")
                return
            frames = [frames[f]]
        else:
            if f > max(frames):
                await msg.edit("Invalid frame. Use `/frames` to check available frames!")
                return
            frames = [f]
    else:
        frames = sprite[layers[0]]["frames"] or sprite[layers[0]]["named_frames"].values()


    for frame in frames:
        filePath = Path(sprite[layers[0]]["root"] + f"{str(frame)}.png")
        im = await colour_image(Image.open(spr / filePath).convert("RGBA"), colour_1)
        for i in layers[1:]:
            if isinstance(i, dict):
                layer = i
            else:
                layer = sprite[i]
            layer_frames = layer["frames"] or layer["named_frames"]
            if frame in layer_frames:
                sproot = layer["root"]
                f = frame
                if "anim_root" in layer and animation_name in layer["anim_root"]:
                    sproot += layer["anim_root"][animation_name]
                if "offset" in layer:
                    f -= layer["offset"] 
                im2 = Image.open(spr / Path(sproot + f"{str(f)}.png")).convert("RGBA")
                im2n = numpy.array(im2)
                im2n = numpy.where(im2n[:, :, 3] > 0)
                if im2n[0].size == 0 and im2n[1].size == 0:
                    im2 = Image.open(spr / Path(layer["root"] + f"{str(f)}.png")).convert("RGBA")
                try:
                    c3test = (int(i) >= 3)
                except (ValueError, TypeError):
                    pass
                col = colour_2 if i == "2" else (colour_3 if c3test else "#ffffff") # Chicory_lagoon has layer four
                im.alpha_composite(await colour_image(im2, col))
        if crop_transparency:
            imnp = numpy.array(im)
            imnp = numpy.where(imnp[:, :, 3] > 0)
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

    if animated:
        await msg.edit(content="Converting PNGs to GIF (2/2)")
        addcrop = f"-crop {crop[2]-crop[0]}x{crop[3]-crop[1]}+{crop[0]}+{crop[1]} +repage " if crop_transparency else ""
        process = await asyncio.create_subprocess_shell(
            f"{imagemagick} -delay 1x{animation_fps} -loop 0 -dispose Background {addcrop}{temp / '*.png'} {temp / 'out.gif'}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if process.returncode != 0: # Error
            await msg.edit(content="<:Pizza_Depressaroli:967482279670718474> Something went wrong (gif conversion error).")
            print(f"GIF CONVERSION ERROR: {process.stderr}")
            try:
                shutil.rmtree(temp)
            except PermissionError:
                print("Failed to delete file.")
            else:
                print(f"Deleted temp: {str(temp)}")
            return
        file = discord.File(temp / "out.gif", f"{name}.gif")
        await msg.edit(content=f"{name} at {animation_fps} fps:", attachments=[file])
        del file # Release out.gif
        try:
            shutil.rmtree(temp)
        except PermissionError:
            print("Failed to delete file.")
        else:
            print(f"Deleted temp: {str(temp)}")
    else:
        imbyte = BytesIO()
        ims.save(imbyte, "PNG")
        imbyte.seek(0)
        file = discord.File(imbyte, f"{name}..png")
        await msg.edit(content=f"{name}{(' frame ' + use_frame) if use_frame else ''}:", attachments=[file])

@tree.command(guild=TEST_GUILD, description="Lists animations for a specific sprite")
async def animations(interaction: discord.Interaction, sprite: str):
    anims = []
    for layer in sprites[sprite]:
        if "anim_root" in sprites[sprite][layer]:
            anims += list(sprites[sprite][layer]["anim_root"])
    await interaction.response.send_message(content=f"Anims: `{'`, `'.join(anims)}`")

@animations.autocomplete("sprite")
async def animations_sprite_autocomplete(interaction: discord.Interaction, current: str):
    lst = []
    for sprite in sprites:
        if current.lower() not in sprite.lower():
            continue
        if [layer for layer in sprites[sprite] if "anim_root" in sprites[sprite][layer]]:
            lst.append(sprite)
            continue
    return [app_commands.Choice(name=i, value=i) for i in lst]

@tree.command(guild=TEST_GUILD, description="Lists frames for a specific sprite")
async def frames(interaction: discord.Interaction, sprite: str):
    if sprite not in sprites:
        await interaction.response.send_message(content="Incorrect Sprite")
        return
    if sprites[sprite]["1"]["frames"]:
        frames = range(len(sprites[sprite]["1"]["frames"]))
    else:
        frames = sprites[sprite]["1"]["named_frames"]
    numbers = []
    strings = []
    for frame in frames:
        try:
            numbers.append(int(frame))
        except ValueError:
            strings.append(frame)
    out = ""
    if numbers:
        out += f"Frames {min(numbers)+1} to {max(numbers)+1}\n"
    if strings:
        out += f"Frames: `{'`, `'.join(strings)}`"
    if not out:
        out = "None"
    await interaction.response.send_message(content=out)

@sprite.autocomplete("sprite")
@frames.autocomplete("sprite")
async def sprite_autocomplete(interaction: discord.Interaction, current: str):
    lst = sorted(list(sprites.keys()) + ["Random"])
    return [app_commands.Choice(name=i, value=i) for i in lst if current.lower() in i.lower()][:25]


@tree.command(guild=TEST_GUILD, description="Get a palette from the game!")
async def palette(interaction: discord.Interaction, palette: str="Random"):
    p = None
    palette = palette.lower()
    if palette == "random":
        palette = random.choice(list(palettes.keys()))
    if palette in palettes.keys():
        p = palettes[palette]
    else:
        await interaction.response.send_message(f"<:Pizza_Awkward:967482807960105062> `{palette}` is not a palette")
        return
    p = [tuple(c) for c in p]
    width = 63
    im = Image.new("RGB", (width*len(p), 20), p[0])
    for i, v in enumerate(p):
        if i == 0:
            continue
        im.paste(Image.new("RGB",(width,20),v), box=(width*i,0))
    fp = BytesIO()
    im.save(fp, format="PNG")
    fp.seek(0)
    file = discord.File(fp, filename="palette.png")
    await interaction.response.send_message(f"{palette}:\n`{'`, `'.join([('#%02x%02x%02x' % i) for i in p])}`", file=file)

@palette.autocomplete("palette")
async def palette_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=i, value=i) for i in sorted(
        [i for i in palettes.keys()] + ["random"]
    ) if current in i][:25]

@tree.command(guild=TEST_GUILD, description="Send a picture of hair to number.")
async def hair(interaction: discord.Interaction):
    await interaction.response.send_message(content="https://cdn.discordapp.com/attachments/947900270992556033/967877113099219004/unknown.png", ephemeral=True)

def is_me():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 105725338541101056
    return app_commands.check(predicate)

@tree.command(guild=TEST_GUILD, description="Death.")
@is_me()
async def die(interaction: discord.Interaction):
    await interaction.response.send_message(content="I hath been slayn.")
    await client.close()

client.run(TOKEN)
