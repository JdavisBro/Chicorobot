import sys
import random
import json
import tempfile
import subprocess
import shutil
from io import BytesIO
from pathlib import Path

import discord
from discord import app_commands
from PIL import Image, ImageChops#, ImageDraw, ImageFont
#from moviepy.editor import ImageSequenceClip
#import numpy

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

@client.event
async def on_ready():
    await tree.sync(guild=TEST_GUILD)
    
    print("LOGGED IN!")

def clamp(value, min, max):
    return min if value <= min else max if value >= max else value

def to_titlecase(string):
    return " ".join([word[0].upper() + word[1:].lower() for word in string.split(" ")])

async def colour_image(im: Image, colour):
    if not isinstance(colour, tuple):
        colour = colour.lstrip("#")
        if colour == "ffffff":
            return im
        colour = tuple([int(colour[i:i+2], 16) for i in (0, 2, 4)] + [255])
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

    im = await colour_image(Image.open(f"sprites/Dog_idle_B/1/{idleFrame:02}.png").resize((750, 750)), body_col)

    if clothes != "Custom":
        if not Path(f"sprites/Dog_body/1/{clothes}.png").exists():
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{clothes}` is not a clothing!")
            return
        im2 = Image.open(f"sprites/Dog_body/1/{clothes}.png").resize((750, 750)) # Clothes
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

    if Path(f"sprites/Dog_body2/1/{clothes}_0.png").exists():
        im.alpha_composite(await colour_image(Image.open(f"sprites/Dog_body2/1/{clothes}_0.png"), hat_col))

    im2 = Image.open(f"sprites/Dog_idle_A/1/{idleFrame:02}.png").resize((750, 750)) # Arm
    im.alpha_composite(await colour_image(im2, body_col))

    if Path(f"sprites/Dog_body2/1/{clothes}_1.png").exists():
        im.alpha_composite(await colour_image(Image.open(f"sprites/Dog_body2/1/{clothes}_1.png"), hat_col))
    
    for h in [hat,hat2]:
        if h in extraHats:
            im.alpha_composite(await colour_image(Image.open(f"sprites/Dog_body2/1/{h}_1.png"), hat_col))

    if not Path(f"sprites/Dog_expression/1/{expression}.png").exists():
        await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{expression}` is not an expression!")
        return
    im2 = Image.open(f"sprites/Dog_expression/1/{expression}.png").resize((750, 750)) # Face
    im.alpha_composite(await colour_image(im2, body_col))    

    if Path(f"sprites/Dog_body2/1/{clothes}_2.png").exists():
        im.alpha_composite( await colour_image( Image.open(f"sprites/Dog_body2/1/{clothes}_2.png"), clothes_col ) )

    for h in [hat,hat2]:
        if Path(f"sprites/Dog_hat/1/Hat/{h}_1.png").exists(): # Behind hair part of hat (only used for horns)
            im.alpha_composite( await colour_image( Image.open(f"sprites/Dog_hat/1/Hat/{h}_1.png"), hat_col ) )

    if all([h in hairHats for h in [hat,hat2]]): # Hat shows hair
        if not Path(f"sprites/Dog_hat/1/Hair/{hair}.png").exists():
            await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{hair}` is not a hair!")
            return
        im.alpha_composite( await colour_image(Image.open(f"sprites/Dog_hat/1/Hair/{hair}.png").resize((750, 750)), body_col ) )

    async def do_hat():
        for h in [hat, hat2]:
            if h == "None" or h in extraHats:
                continue
            if h != "Custom":
                im2 = Image.open(f"sprites/Dog_hat/1/Hat/{h}.png").resize((750, 750)) # Hat
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
        im2 = Image.open("sprites/Dog_idle_ear/1/03.png").resize((750, 750)) # Ear
        im.alpha_composite(await colour_image(im2, body_col))

    for h in [hat, hat2]:
        if h == "None" or h == "Custom" or h in extraHats:
            continue
        if not Path(f"sprites/Dog_hat/1/Hat/{h}.png").exists():
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
        random.choice([i.name[:-4] for i in Path("sprites/Dog_expression/1/").iterdir()]),
        random.choice([i.name[:-4] for i in Path("sprites/Dog_body/1/").iterdir()]),
        random.choice([i.name[:-4] for i in Path("sprites/Dog_hat/1/Hat/").iterdir()] + extraHats + ["None"]),
        random.choice([i.name[:-4] for i in Path("sprites/Dog_hat/1/Hair/").iterdir()]),
        "None" if not add_hat2 else random.choice([i.name[:-4] for i in Path("sprites/Dog_hat/1/Hat/").iterdir()] + extraHats + ["None"]),
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
    ls = sorted([
        i.name[:-4]
        for i in Path("sprites/Dog_body/1/").iterdir()
    ] + ["Custom"])
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("expression")
async def expression_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted([
        i.name[:-4]
        for i in Path("sprites/Dog_expression/1/").iterdir()
    ])
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

@dog.autocomplete("hat")
@dog.autocomplete("hat2")
async def hat_autocomplete(interaction: discord.Interaction, current: str):
    ls = sorted([
        i for i in ([i.name[:-4] for i in Path("sprites/Dog_hat/1/Hat/").iterdir()] + ["None", "Custom"] + extraHats) if current.lower() in i.lower()
    ])
    if "Horns_1" in ls:
        ls.remove("Horns_1")
    return [app_commands.Choice(name=i, value=i) for i in ls][:25]

@dog.autocomplete("hair")
async def hair_autocomplete(interaction: discord.Interaction, current:str):
    ls = sorted([
        i.name[:-4] for i in Path("sprites/Dog_hat/1/Hair/").iterdir() if current.lower() in i.name.lower()
    ])
    return [app_commands.Choice(name=i, value=i) for i in ls][:25]


@tree.command(guild=TEST_GUILD, description="Show a sprite.")
async def sprite(interaction: discord.Interaction, sprite: str, animated: bool=False):
    if animated and not imagemagick:
        await interaction.response.send_message(content="Animated sprites are unavailable, making non animated version.")
        animated = False
    else:
        await interaction.response.defer()
    if sprite.lower() == "random":
        sprite = random.choice([i.name for i in Path("sprites/").iterdir()])
    ims = []
    spriteDir = Path(f"sprites/{sprite}/")
    layers = [i for i in spriteDir.iterdir()]
    if sprite.endswith("_A"):
        layers += [i/"1" for i in Path("sprites/").glob("_".join(sprite.split("_")[:-1])+"_*") if i != spriteDir]
    i = 0
    for filePath in layers[0].iterdir():
        im = Image.open(filePath).convert("RGBA")
        for layer in layers[1:]:
            name = filePath.name
            if (layer / name).exists():
                im2 = Image.open(layer / name).convert("RGBA")
                im.alpha_composite(im2)
        ims.append(im)
        if not animated:
            break
    if animated:
        name = tempfile.mkdtemp()
        name = Path(name)
        msg = await interaction.followup.send(content="Saving PNGs.")
        for i, im in enumerate(ims):
            im.save(name / f"{i:02}.png")
        await msg.edit(content="Converting to gif.")
        process = subprocess.Popen(f"{imagemagick} -delay 10 -loop 0 -dispose Background {name / '*.png'} {name / 'out.gif'}",shell=True)
        if process.wait() != 0:
            await msg.edit(content="<:Pizza_Depressaroli:967482279670718474> Something went wrong (gif conversion error).")
            return
        file = discord.File(name / "out.gif", f"{sprite}.gif")
        await msg.edit(content=f"{sprite}:", attachments=[file])
        del file
        try:
            shutil.rmtree(name)
        except PermissionError:
            print("Failed to delete file.")
    else:
        imbyte = BytesIO()
        ims[0].save(imbyte, "PNG")
        imbyte.seek(0)
        file = discord.File(imbyte, f"{sprite}..png")
        await interaction.followup.send(content=f"{sprite}:", file=file)

# @say.autocomplete("font")
# async def font_autocomplete(interaction: discord.Interaction, current: str):
#     return [
#         app_commands.Choice(i, i)
#         for i in ["g","gg"] if current.lower() in i 
#     ]

@sprite.autocomplete("sprite")
async def sprite_autocomplete(interaction: discord.Interaction, current: str):
    lst = [
        i.name
        for i in Path("sprites/").iterdir()
    ] + ["Random"]
    return [app_commands.Choice(name=i, value=i) for i in lst if current.lower() in i.lower()][:25]

@dog.error
@random_dog.error
@sprite.error
async def dog_error(interaction: discord.Interaction, error):
    if not interaction.response.is_done():
        await interaction.response.send_message("<:Pizza_Depressaroli:967482279670718474> Something went wrong.")
    else:
        await interaction.followup.send("<:Pizza_Depressaroli:967482279670718474> Something went wrong.")
    raise getattr(error,"original",error)

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

client.run(TOKEN)
