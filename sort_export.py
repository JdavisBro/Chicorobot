import json
import shutil
from pathlib import Path

#
# Sorts an Export_Sprites into a sprites.json, run this to generate a new sprites.json
#

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
    "Splashpants",
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

duplicates = {
    "Black Tee": [
        "Kerchief",
        "Scarf",
        "Shawl",
        "Spike",
    ],
    "Black Dress": [
        "Studs",
    ]
}

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
    "Hair/Simple",
    "Hair/Flip",
    "Hair/Floofy",
    "Hat/Headband",
    "Hat/Bow",
    "Hair/Big Fluffy",
    "Hair/Gorgeous",
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
    "Hair/Mullet",
    "Hair/Bowl",
    "Hair/Pony",
    "Hair/Hedgehog",
    "Hair/Boyband",
    "Hair/Shaved",
    "Hair/Shortcurl",
    "Hair/Pixie",
    "Hair/Bob",
    "Hair/Anime",
    "Hair/Dreds",
    "Hair/Fuzz",
    "Hair/Fro",
    "Hair/Emo",
    "Hair/Pigtails",
    "Hair/Pompadour",
    "Hair/Spikehawk",
    "Hair/Flame",
    "Hair/Topknot",
    "Hair/Bellhair",
    "Hair/Hawk",
    "Hair/Longpony",
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
    "Hair/Highback",
    "Hair/Swoosh",
    "Hair/Mofro",
    "Hair/Poodle",
    "Hair/Frizz",
    "Hair/Curleye"
]

dogExpressions = [
    "small",
    "closed",
    "grin",
    "angry",
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
    with open("data/sprites.json", "w+") as f:
        json.dump(spritesDict, f, sort_keys=True)

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

    if sprite == "Logo":
        if layer_anim in ["jp", "kr", "sch", "tch"]:
            sprite = "Logo_alt"

    if sprite in ["Chicoryportrait", "Castleportrait", "Finaltreearm", "Linefx", "Oozewiggle", "Queen_antennaA", "Queen_antennaB", "Townflowers", "Townpath"]:
        sprite = sprite + "_" + str(layer)
        if sprite.startswith("Chicoryportrait"):
            layer = frame + 1
            frame = 0
        else:
            layer = 1

    if sprite == "Logo" and layer == 2:
        frame += 8

    if sprite == "Dog_hat":
        if dogHat[frame].split("/")[0] == "Hair":
            sprite = "Dog_hair"

    if sprite not in spritesDict:
        spritesDict[sprite] = {}

    if layer not in spritesDict[sprite]:
        spritesDict[sprite][layer] = {}
        if layer != 1 and not sprite.startswith("Chicoryportrait"):
            if sprite == "Logo_alt":
                spritesDict[sprite][layer]["root"] = f"sprLogo_{'layer' if layer_text else ''}{layer}_"
            else:
                spritesDict[sprite][layer]["root"] = f"spr{sprite}_{'layer' if layer_text else ''}{layer}_"
        else:
            spritesDict[sprite][layer]["root"] = f"spr{sprite}_"
        if sprite in ["Dog_body", "Dog_body2", "Dog_hat", "Dog_hair", "Dog_expression"]:
            spritesDict[sprite][layer]["named_frames"] = {}
            spritesDict[sprite][layer]["frames"] = None
        else:
            spritesDict[sprite][layer]["frames"] = []

    if sprite == "Dog_body":
        if dogClothes[frame] in duplicates.keys():
            for name in duplicates[dogClothes[frame]]:
                spritesDict[sprite][layer]["named_frames"][name] = frame
        spritesDict[sprite][layer]["named_frames"][dogClothes[frame]] = frame
    elif sprite == "Dog_body2":
        spritesDict[sprite][layer]["named_frames"][dogClothes2[frame]] = frame
    elif sprite == "Dog_hat":
        spritesDict[sprite][layer]["named_frames"][dogHat[frame].split("/")[1]] = frame
    elif sprite == "Dog_hair":
        spritesDict[sprite][layer]["named_frames"][dogHat[frame].split("/")[1]] = frame
        spritesDict[sprite][layer]["root"] = f"sprDog_hat_"
    elif sprite == "Dog_expression":
        spritesDict[sprite][layer]["named_frames"][dogExpressions[frame]] = frame
    else: 
        if frame not in spritesDict[sprite][layer]["frames"]:
            spritesDict[sprite][layer]["frames"].append(frame)
        if sprite == "Logo_alt" and frame == 18:
            spritesDict[sprite][layer]["frames"] += [19, 20, 21, 22, 23]

    if layer_anim:
        if "anim_root" not in spritesDict[sprite][layer]:
            spritesDict[sprite][layer]["anim_root"] = {}
        if sprite == "Pickle" and layer_anim == "blink":
            spritesDict[sprite][layer]["anim_root"]["sit_blink"] = f"{layer_anim}_"
        else:
            spritesDict[sprite][layer]["anim_root"][layer_anim] = f"{layer_anim}_"
            if sprite == "Mom":
                spritesDict[sprite][layer]["anim_root"][layer_anim+"_move"] = f"{layer_anim}_"
            elif sprite == "Pistachio" and layer_anim == "smile":
                spritesDict[sprite][layer]["anim_root"]["sit_smile"] = f"{layer_anim}_"

    if sprite == "Chicory_ok" and layer == 4:
        for spr in ["Chicory_idle", "Chicory_postgame", "Chicory_postgame2"]:
            if spr not in spritesDict:
                spritesDict[spr] = {}
            if layer not in spritesDict[spr]:
                spritesDict[spr][layer] = {}
                spritesDict[spr][layer]["root"] = "sprChicory_ok_layer4_"
                spritesDict[spr][layer]["frames"] = []
            if frame not in spritesDict[spr][layer]["frames"]:
                spritesDict[spr][layer]["frames"].append(frame)
            if "anim_root" in spritesDict[sprite][layer]:
                spritesDict[spr][layer]["anim_root"] = spritesDict[sprite][layer]["anim_root"]
    
    spriteSpeeds = {
        "Blackberry" : 1.25,
        "Boss3": 1.5,
        "Boss6": 1.25,
        "BossStealTransform": 1.5, # CHECK
        "Turnip": 1.25, # objCaveblocker
        "Chicory_lagoon": 0.75,
        "Chicory_partner": 2,
        "Chicory_curl": 0.5, # Except Turn Animation
        "Feastbug_fly1": 2,
        "Fattk_curve": 2,
        "Fattk_leafa": 1.5,
        "Fattk_leafb": 1.5,
        "Fattk_line": 2,
        # sprFinalboss_finalform_roots: FinalPaintPiece Step 2 <-- do this? later?
        "Lost_kitten": 1.5,
        "Finjilogo": 3,
        "Hermitcrab": 1.5,
        "Letterbugs": 1.5,
        "Oats": 1, # ( ( 12 / (beatFrames() * 2) ) * 7.5 ) fuck you # <-- do this? later?
        "Endpetal": 1.1,
        "Rice": 1.25
    }

    if sprite in spriteSpeeds.keys():
        spritesDict[sprite][1]["speed"] = spriteSpeeds[sprite]

    if sprite == "Logo" and layer == 2 and not layer_anim:
        if not "anim_root" in spritesDict[sprite][layer]:
            spritesDict[sprite][layer]["anim_root"] = {}
        spritesDict[sprite][layer]["anim_root"]["en"] = ""
        spritesDict[sprite][layer]["offset"] = 8

if __name__ == "__main__":
    main()