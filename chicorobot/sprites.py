import asyncio
import json
from pathlib import Path
from typing import Union

import discord
from PIL import Image, ImageChops

from chicorobot import errors

__all__ = (
    "Sprites",
    "Sprite",
    "Layer",
    "sprites",
    "colour_image",
    "dog_animations"
)

spr = Path("Export_Sprites/")
gayim = Image.open("chicorobot/gay.png").convert("RGBA")
chicorim = Image.open("chicorobot/chicory.png").convert("RGBA")

async def colour_image(im, colour):
    if isinstance(colour, str): # String, Hex/Image
        if colour.lstrip("#") == "gay":
            return ImageChops.multiply(im, gayim.resize(im.size))
        if colour.lstrip("#") == "chicory":
            return ImageChops.multiply(im, chicorim.resize(im.size))
        colour = colour.lstrip("#").lower()
        if colour == "ffffff": # WHITE, no need to colour :D
            return im
        try:
            colour = tuple([int(colour[i:i+2], 16) for i in (0, 2, 4)] + [255])
        except ValueError:
            raise errors.ColourError()
    else: # Tuple
        if isinstance(colour, discord.Colour):
            colour = colour.to_rgb()
        if colour == (255, 255, 255): # WHITE, no need to colour :D
            return im
        colour = tuple(list(colour) + [255])
    return ImageChops.multiply(im, Image.new("RGBA", im.size, colour))

class Sprites():
    def __init__(self, spriteDict):
        self._dict = spriteDict
        self.body2 = Layer(1, self._dict["Dog_body2"]["1"])
        self.body = Layer(1, self._dict["Dog_body"]["1"])
        self.hat = Layer(1, self._dict["Dog_hat"]["1"])
        self.hair = Layer(1, self._dict["Dog_hair"]["1"])
        self.expression = Layer(1, self._dict["Dog_expression"]["1"])
        self.head = Layer(1, self._dict["Dog_head"]["1"])

    def __getitem__(self, key):
        if key not in self._dict:
            raise errors.SpriteNotFound(key)
        return Sprite(self._dict[key])

    def sprites(self):
        return sorted([i for i in self._dict.keys()])

class Sprite():
    def __init__(self, data):
        self._dict = data

    def __getitem__(self, key):
        if key not in self._dict:
            raise errors.LayerNotFound(key)
        return Layer(int(key), self._dict[key])

    def get_layers(self):
        return [i for i in self._dict]

    @property
    def layer(self):
        return Layer(1, self._dict["1"])

class Layer():
    def __init__(self, num, data):
        self.num = num
        self._dict = data
        self.root = data["root"]
        self.frames = data["frames"]
        if "named_frames" in data:
            self.named_frames = data["named_frames"]
        else:
            self.named_frames = None
        if "anim_root" in data:
            self.anim_root = data["anim_root"]
        else:
            self.anim_root = None
        if "offset" in data:
            self.offset = data["offset"]
        else:
            self.offset = None
        if "speed" in data:
            self.speed = data["speed"]
        else:
            self.speed = 1

    def __lt__(self, other):
        if isinstance(other, Layer):
            return sorted([self.root, other.root])[0] == other.root
        return False

    def get_frames(self):
        return self.frames or [i for i in self.named_frames]
    
    def is_anim(self, anim):
        if self.anim_root and anim:
            return anim in self.anim_root
        return False

    def is_frame(self, frame):
        if self.frames:
            try:
                frame = int(frame)
            except ValueError:
                return False
            return frame < len(self.frames)
        else:
            return frame in self.named_frames.keys()

    def get_frame(self, frame, anim=None):
        frame = str(frame)
        root = self.root
        if self.anim_root and anim:
            if anim in self.anim_root:
                root += self.anim_root[anim]
        if self.frames:
            try:
                frame = int(frame)
            except ValueError:
                raise errors.FrameNotFound(frame) 
            if frame >= len(self.frames):
                raise errors.FrameNotFound(frame)

            if root == "sprLogo_alt_" and frame >= 15:
                frame = 15 + (((frame - 19) % 4)//2) # Alternate 15 to 18
            
            if root.startswith("sprChicoryportrait"):
                frame = 4 - self.num
            return root + str(frame)
        else:
            if frame not in self.named_frames:
                raise errors.FrameNotFound(frame)
            return root + str(self.named_frames[frame])

    def get_frame_path(self, frame, anim=None):
        return spr / (self.get_frame(frame, anim) + ".png")

    async def load_frame(self, frame, anim=None, resize: tuple=False, colour: Union[str, tuple]=None):
        # Get Path & Load Image
        path = self.get_frame_path(frame, anim)
        if path.exists():
            im = Image.open(path)
        else:
            impath = self.get_frame_path(int(frame) - 1, anim)
            if not impath.exists():
                impath = self.get_frame_path(frame)
                if not impath.exists():
                    if self.anim_root:
                        impath = self.get_frame_path(frame, list(self.anim_root.keys())[0])
                    if not impath.exists():
                        raise errors.FrameNotFound(frame)
            im = Image.open(impath)
        # Resize
        if resize:
            im = im.resize(resize)
        # Colour
        if not colour:
            return im
        return await colour_image(im, colour)

with open("data/sprites.json") as f:
    sprites = Sprites(json.load(f))

with open("data/dog_animations.json") as f:
    dog_animations = json.load(f)
