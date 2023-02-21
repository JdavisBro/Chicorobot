import json
from pathlib import Path

from chicorobot.sprites import sprites

__all__ = (
    "palettes",
    "prop_animations",
    "all_colours",
    "randomablePalettes",
    "hairHats",
    "hatOverEar",
    "extraHats",
    "paletteAliases",
    "expressions_alts",
    "in_game_clothes",
    "in_game_hats"
)

with Path("data/palettes.json").open("r") as f:
    palettes = json.load(f)

with Path("data/prop_animations.json").open("r") as f:
    prop_animations = json.load(f)

for sprite in sprites.sprites():
    anims = []
    spr = sprites[sprite]
    for layer in spr.get_layers():
        if spr[layer].anim_root:
            for anim in spr[layer].anim_root:
                if anim not in anims:
                    anims.append(anim)
    for anim in anims:
        if sprite not in prop_animations:
            prop_animations[sprite] = {}
        if anim not in prop_animations[sprite]:
            if sprite == "Mom" and "move" in anim:
                prop_animations[sprite][anim] = prop_animations[sprite]["idle_move"]
            elif "sit" in anim and "sit" in prop_animations[sprite]:
                prop_animations[sprite][anim] = prop_animations[sprite]["sit"]
            elif "idle" in prop_animations[sprite]:
                prop_animations[sprite][anim] = prop_animations[sprite]["idle"]
            else:
                prop_animations[sprite][anim] = {"frames": {"start": 0, "end": len(spr.layer.get_frames())-1, "holds": -1, "sounds": -1}, "loop": 0, "bounce": 0}

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

paletteAliases = {
    "Luncheon": "town",
    "Luncheon Spooky": "town_spooky",
    "Luncheon Spooky 2": "town_spooky2",
    "Luncheon Postgame": "town_postgame",
    "Boss 1": "boss1",
    "Boss 2": "boss2",
    "Brekkie": "brekkie",
    "Brunch Canyon": "brunch",
    "Caves": "cave",
    "Dinners": "dinners",
    "Elevenses": "elevenses",
    "Feast": "feast",
    "Appie Foothills": "foothills",
    "Supper Woods": "forest",
    "Gray": "gray",
    "Grub Caverns": "grub1",
    "Grub Deep": "grub2",
    "Spoons Island": "island",
    "Teatime Meadows": "meadows",
    "Dessert Mountain": "mtn",
    "Newgame": "newgame",
    "Nibble Tunnel": "nibble",
    "Ocean": "ocean",
    "Dessert Mountain Peak": "peak",
    "Potluck": "potluck",
    "Banquet Rainforest": "rainforest",
    "Sips River": "river",
    "Wielder Temple": "ruins",
    "Wielder Temple Dark": "ruins_dark",
    "Spooky": "spooky",
    "Simmer Springs": "springs",
    "Gulp Swamp": "swamp"
}

expressions_alts = {
    "grr": "angry",
    "gr": "angry",
    "grrr": "angry",
    "gah": "gasp",
    "ow": "ouch",
    "worried": "worry",
    "swoon": "smit",
    "hmf": "hmph"
}

in_game_clothes = {
    "Custom Tee": "Custom",
    "Fuzzy": "Woven",
    "Splashpants": "Splash Pants",
    "Princess": "Gorgeous",
    "Gi": "Hiker"
}

in_game_hats = {
    "Custom Hat": "Custom",
    "Wielder Tie": "Wielder Wrap",
    "Hajib": "Headscarf",
    "Earflap": "Earflaps"
}
