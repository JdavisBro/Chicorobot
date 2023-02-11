import json
from pathlib import Path

with Path("data/palettes.json").open("r") as f:
    palettes = json.load(f)

with Path("data/prop_animations.json").open("r") as f:
    prop_animations = json.load(f)

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
