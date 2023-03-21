from pathlib import Path

import discord
from discord import app_commands

from chicorobot.sprites import *
from chicorobot.assets import *

async def sprite(interaction: discord.Interaction, current: str): # frames, sprite
    lst = sorted(list(sprites.sprites()) + ["Random"])
    return [app_commands.Choice(name=i, value=i) for i in lst if current.lower() in i.lower()][:25]

async def area_name(interaction: discord.Interaction, current: str): # palette
    lst = [i for i in sorted([i for i in paletteAliases.keys()] + ["Random"]) if current.lower() in i.lower()][:25]
    return [app_commands.Choice(name=i, value=i) for i in lst]

async def random_palette(interaction: discord.Interaction, current: str): # random_dog
    lst = [i for i in (["None", "Random"] + sorted(paletteAliases.keys())) if current.lower() in i.lower()][:25]
    return [app_commands.Choice(name=i, value=i) for i in lst]

async def code_name(interaction: discord.Interaction, current: str): # palette
    return [app_commands.Choice(name=i, value=i) for i in sorted(
        [i for i in palettes.keys()] + ["random"]
    ) if current in i][:25]


async def cog(interaction: discord.Interaction, current: str):
    if interaction.user.id != interaction.client.ownerid:
        return [app_commands.Choice(name="You shouldn't be here......", value="what")]
    else:
        coglist = ["sprite", "utils", "dog", "save"]
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

async def animation(interaction: discord.Interaction, current:str): # DOG ANIMATIONS
    return [app_commands.Choice(name=i, value=i) for i in dog_animations.keys() if current.lower() in i][:25]

async def animations_sprite(interaction: discord.Interaction, current: str): # PROP ANIMATIONS
    return [app_commands.Choice(name=i, value=i) for i in prop_animations.keys() if current.lower() in i.lower()][:25]

async def animation_seq(interaction: discord.Interaction, current:str):
    sprite = str(interaction.namespace["sprite"])
    onincorrect = []
    if current:
        onincorrect.append(app_commands.Choice(name=current, value=current))
    if sprite not in sprites.sprites():
        return onincorrect+[app_commands.Choice(name=f"Sprite {sprite} not found.", value="teehee ;)")]
    if sprite not in prop_animations.keys():
        return onincorrect+[app_commands.Choice(name=f"Sprite {sprite} has no animations.", value="teehee ;)")]
    current = current.split(";")
    anim = current[-1]
    anims = prop_animations[sprite].keys()
    for i, cur in enumerate(current[:-1]):
        if cur not in anims:
            return [app_commands.Choice(name=";".join(current), value=";".join(current)), app_commands.Choice(name=f"Animation number {i+1} ({cur}) not found.", value="teehee ;)")]
    suggest = []
    for i in anims:
        if anim in i:
            c = current[:-1]
            c.append(i)
            suggest.append(";".join(c))
    return [app_commands.Choice(name=i, value=i) for i in suggest][:25]