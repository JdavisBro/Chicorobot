import shutil
from pathlib import Path

dogClothes = [
    "Overalls",
    "Flower Dress",
    "Hoodie",
    "Pocket Jacket",
    "Starry Tee",
    "Stripey Tee",
    "Sunny Tee",
    "Bolt Tee",
    "Moon Tee",
    "Big Star",
    "Black Tee",
    "Bee",
    "Big Flower",
    "High Nooner",
    "Dot Dress",
    "Cord Coat",
    "Puffy Jacket",
    "Dorky",
    "Woven",
    "Rex Bod",
    "Wielder Cloak",
    "Hotneck",
    "Gothy",
    "Nice Shirt",
    "Smock",
    "Island",
    "Splash Pants",
    "Splash Onesie",
    "College",
    "Biker Jacket",
    "Mascot Bod",
    "Avast",
    "Mailbag",
    "Bard", #
    "Tux", #
    "Scientist",
    "Fuzzy Jacket",
    "Sailor",
    "Sequins",
    "Black Dress",
    "Leafy",
    "Pajamas",
    "Cute Dress",
    "Pilot",
    "Shell Tee",
    "Big Heart",
    "Robo",
    "Ski Jacket",
    "Gorgeous",
    "Royal", #
    "Hiker" #
]

blackTeeDuplicates = [
    "Kerchief",
    "Scarf",
    "Shawl",
    "Spike",
]

dogClothes2 = [ # 0, 1 = hat colour, 1 = Under head above arm, 2 = Fit colour and above head
    "_IDK", # no clue
    "Kerchief_1", # 1, hat
    "Scarf_1", # 1, hat
    "Cord Coat_2", # 2, fit
    "Wielder Cloak_1", # 1, hat
    "Bard_2", # 2, fit
    "Fuzzy Jacket_2", #2, fit
    "_Headphones",
    "Sailor_1", # 1, hat
    "Shawl_1", # 1, hat
    "Spike_1", # 1, hat
    "Studs_1", # 1, hat
    "Ski Jacket_2", # 2, fit
    "Gorgeous_0", # 0, hat
    "Royal_2", # 2, fit
    "Hiker_0" # 0, hat
]

dogHat = [
    "Hat/Bandana",
    "Hat/Beanie",
    "Hat/Brimcap",
    "Hat/Strawhat",
    "Hat/Sunhat",
    "Hair/00",
    "Hair/01",
    "Hair/02",
    "Hat/Headband",
    "Hat/Bow",
    "Hair/03",
    "Hair/04",
    "Hat/Antenna",
    "Hat/Flower",
    "Hat/Howdy",
    "Hat/Shades",
    "Hat/Tinted Shades",
    "Hat/Line Shades",
    "Hat/Big Shades",
    "Hat/Beret",
    "Hat/Rex Head",
    "Hat/Wielder Wrap",
    "Hat/Newsie",
    "Hat/Half-Moons",
    "Hat/Round Glasses",
    "Hat/Square Glasses",
    "Hat/Pointish Glasses",
    "Hat/Spellcaster",
    "Hat/Backwards",
    "Hat/Feather",
    "Hat/Ahoy",
    "Hat/Delivery",
    "Hat/Earmuffs",
    "Hat/Clown",
    "Hat/Wintry",
    "Hat/Eyepatch",
    "Hat/Gnome",
    "Hat/Mascot Head",
    "Hat/Spike Helmet",
    "Hat/Big Fungus",
    "Hat/Nautical",
    "Hat/Fungus",
    "Hat/Goggles",
    "Hat/Chef",
    "Hat/Foxy",
    "Hat/Sparkles",
    "Hat/Aviators",
    "Hat/Beak",
    "Hat/Rim Shades",
    "Hat/Bell",
    "Hat/Elf",
    "Hat/Gardener",
    "Hat/Stache",
    "Hat/Monocle",
    "Hat/Stormy",
    "Hat/Superstar",
    "Hair/05",
    "Hair/06",
    "Hair/07",
    "Hair/08",
    "Hair/09",
    "Hair/10",
    "Hair/11",
    "Hair/12",
    "Hair/13",
    "Hair/14",
    "Hair/15",
    "Hair/16",
    "Hair/17",
    "Hair/18",
    "Hair/19",
    "Hair/20",
    "Hair/21",
    "Hair/22",
    "Hair/23",
    "Hair/24",
    "Hair/25",
    "Hair/26",
    "Hat/Headphones",
    "Hat/Headscarf",
    "Hat/Skate Helmet",
    "Hat/Mask",
    "Hat/Top Hat",
    "Hat/Helm",
    "Hat/Beard",
    "Hat/Crown",
    "Hat/Earflaps",
    "Hat/Tiara",
    "Hat/Horns",
    "Hat/Horns_1",
    "Hair/27",
    "Hair/28",
    "Hair/29",
    "Hair/30",
    "Hair/31",
    "Hair/32"
]

dogExpressions = [
    "small",
    "closed",
    "grin",
    "grr",
    "nervous",
    "gasp",
    "heee",
    "whoa",
    "sorry",
    "stop",
    "ouch",
    "worry",
    "knockdown",
    "smit",
    "smile",
    "cheeky",
    "hmpf",
    "okay",
    "evil",
    "depressed",
    "embarrass",
    "closed sad"
]

def main():
    spritesDir = Path("Export_Sprites/")
    newDir = Path("sprites/")
    if newDir.exists():
        shutil.rmtree(str(newDir))
    newDir.mkdir()
    for impath in spritesDir.glob("spr*.png"):
        name = impath.stem.split("_")
        sprite = ""
        layer = 1
        frame = 0
        for i, v in enumerate(name):
            if i == 0:
                sprite += v[3:]
            else:
                if v.startswith("layer"):
                    layer = int(v.replace("layer",""))
                    break
                try: # Layer 0, Frame Number
                    int(v)
                except ValueError:
                    pass
                else:
                    break
                sprite += "_" + v
        frame = int(name[-1])
        newimpath = newDir / sprite / str(layer)
        if sprite == "Dog_body":
            if dogClothes[frame] == "Black Tee":
                for name in blackTeeDuplicates:
                    newimpath.mkdir(parents=True, exist_ok=True)
                    shutil.copy(impath, newimpath / f"{name}.png")
            newimpath = newimpath / f"{dogClothes[frame]}.png"
        elif sprite == "Dog_body2":
            newimpath = newimpath / f"{dogClothes2[frame]}.png"
        elif sprite == "Dog_hat":
            newimpath = newimpath / f"{dogHat[frame]}.png"
        elif sprite == "Dog_expression":
            newimpath = newimpath / f"{dogExpressions[frame]}.png"
        else:
            newimpath = newimpath / f"{frame:02}.png"
        newimpath.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(impath , newimpath)
        print(str(newimpath))

if __name__ == "__main__":
    main()