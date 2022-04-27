import json
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
    "IDK_2", # no clue
    "Kerchief_1", # 1, hat
    "Scarf_1", # 1, hat
    "Cord Coat_2", # 2, fit
    "Wielder Cloak_1", # 1, hat
    "Bard_2", # 2, fit
    "Fuzzy Jacket_2", #2, fit
    "Neck_Headphones_1",
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

decoDict = {} # Coming soon

spritesDict = {}

def main():
    spritesDir = Path("Export_Sprites/")
    for impath in sorted(spritesDir.iterdir(), key=lambda f: f"{'_'.join(f.stem.split('_')[:-1])}_{int(f.stem.split('_')[-1]):03}" ):
        if not impath.name.endswith(".png"):
            continue
        if impath.stem.startswith("spr") and not impath.stem.startswith("sprite"):
            add_sprite(impath)
        else:
            add_deco(impath)
    with open("sprites.json", "w+") as f:
        json.dump(spritesDict, f)

def add_deco(path):
    pass

def add_sprite(path):
    name = path.stem[3:].split("_")
    sprite = ""
    layer = 1
    layer_text = False
    layer_anim = None
    frame = 0
    for i, v in enumerate(name):
        if i == 0:
            sprite += v
        else:

            if v.startswith("layer"):
                layer = int(v.replace("layer",""))
                layer_text = True
                if (len(name) - i - 1) > 1: # More than 1 remaining thing
                    layer_anim = "_".join(name[i+1:-1])
                    break
            else:
                try: # Layer 0, Frame Number
                    int(v)
                except ValueError:
                    sprite += "_" + v
                else:
                    if i+1 != len(name): # If this isn't the last one this is a layer
                        layer = int(v)
                        layer_anim = "_".join(name[i+1:-1])
                        break

    frame = int(name[-1])

    if sprite == "Logo" and layer == 2:
        frame += 8

    if sprite == "Dog_hat":
        if dogHat[frame].split("/")[0] == "Hair":
            sprite = "Dog_hair"

    if sprite not in spritesDict:
        spritesDict[sprite] = {}

    if layer not in spritesDict[sprite]:
        spritesDict[sprite][layer] = {}
        if layer != 1:
            spritesDict[sprite][layer]["root"] = f"spr{sprite}_{'layer' if layer_text else ''}{layer}_"
        else:
            spritesDict[sprite][layer]["root"] = f"spr{sprite}_"
        if sprite in ["Dog_body", "Dog_body2", "Dog_hat", "Dog_hair", "Dog_expression"]:
            spritesDict[sprite][layer]["named_frames"] = {}
            spritesDict[sprite][layer]["frames"] = None
        else:
            spritesDict[sprite][layer]["frames"] = []

    if sprite == "Dog_body":
        if dogClothes[frame] == "Black Tee":
            for name in blackTeeDuplicates:
                spritesDict[sprite][layer]["named_frames"][name] = frame
        spritesDict[sprite][layer]["named_frames"][dogClothes[frame]] = frame
    elif sprite == "Dog_body2":
        spritesDict[sprite][layer]["named_frames"][dogClothes2[frame]] = frame
    elif sprite == "Dog_hat":
        spritesDict[sprite][layer]["named_frames"][dogHat[frame].split("/")[1]] = frame
    elif sprite == "Dog_hair":
        spritesDict[sprite][layer]["named_frames"][int(dogHat[frame].split("/")[1])] = frame
        spritesDict[sprite][layer]["root"] = f"sprDog_hat_"
    elif sprite == "Dog_expression":
        spritesDict[sprite][layer]["named_frames"][dogExpressions[frame]] = frame
    elif layer_anim:
        if "anim_root" not in spritesDict[sprite][layer]:
            spritesDict[sprite][layer]["anim_root"] = {}
        spritesDict[sprite][layer]["anim_root"][layer_anim] = f"{layer_anim}_"
    else: 
        spritesDict[sprite][layer]["frames"].append(frame)

    if sprite == "Logo" and layer == 2 and not layer_anim:
        if not "anim_root" in spritesDict[sprite][layer]:
            spritesDict[sprite][layer]["anim_root"] = {}
        spritesDict[sprite][layer]["anim_root"]["en"] = ""
        spritesDict[sprite][layer]["offset"] = 8

    if sprite == "Finalboss_finalform":
        print(f"{'_'.join(path.stem.split('_')[:-1])}_{int(path.stem.split('_')[-1]):03}" )

if __name__ == "__main__":
    main()