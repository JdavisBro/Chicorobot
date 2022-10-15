import discord
from discord import app_commands

from chicorobot.sprites import *
from chicorobot.assets import *

async def sprite(interaction: discord.Interaction, current: str): # frames, sprite
    lst = sorted(list(sprites.sprites()) + ["Random"])
    return [app_commands.Choice(name=i, value=i) for i in lst if current.lower() in i.lower()][:25]

async def area_name(interaction: discord.Interaction, current: str): # palette
    lst = [i for i in sorted(
        [i for i in paletteAliases.keys()] + ["Random"]
    ) if current in i][:25]
    return [app_commands.Choice(name=i, value=i) for i in lst]

async def random_palette(interaction: discord.Interaction, current: str): # random_dog
    lst = [i for i in (["None", "Random"] + sorted(paletteAliases.keys())) if current.lower() in i.lower()][:25]
    return [app_commands.Choice(name=i, value=i) for i in lst]

async def code_name(interaction: discord.Interaction, current: str): # palette
    return [app_commands.Choice(name=i, value=i) for i in sorted(
        [i for i in palettes.keys()] + ["random"]
    ) if current in i][:25]

async def animations_sprite(interaction: discord.Interaction, current: str): # animations
    lst = []
    for sprite in sprites.sprites():
        if current.lower() not in sprite.lower():
            continue
        if [layer for layer in sprites[sprite].get_layers() if sprites[sprite][layer].anim_root]:
            lst.append(sprite)
            continue
    return [app_commands.Choice(name=i, value=i) for i in lst]

async def cog(interaction: discord.Interaction, current: str):
    if interaction.user.id != interaction.client.ownerid:
        return [app_commands.Choice(name="You shouldn't be here......", value="what")]
    else:
        coglist = ["sprite", "utils", "dog"]
        return [app_commands.Choice(name=i, value=i) for i in coglist if current in i]

# dog autocompletes
async def expression(interaction: discord.Interaction, current: str):
    ls = ["normal"] + sorted([i.stem for i in Path("expressions/").iterdir()], key=lambda i: i.replace("custom ", "z"))
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

async def clothes(interaction: discord.Interaction, current: str):
    ls = sorted(sprites.body.get_frames() + ["Custom"])
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

async def hat(interaction: discord.Interaction, current: str):
    ls = sorted(sprites.hat.get_frames() + ["None", "Custom"] + extraHats)
    if "Horns_1" in ls:
        ls.remove("Horns_1")
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

async def hair(interaction: discord.Interaction, current:str):
    ls = sorted(sprites.hair.get_frames())
    return [app_commands.Choice(name=i, value=i) for i in ls if current.lower() in i.lower()][:25]

async def animation(interaction: discord.Interaction, current:str):
    return [app_commands.Choice(name=i, value=i) for i in dog_animations.keys() if current.lower() in i][:25]
