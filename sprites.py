import asyncio
import json
from pathlib import Path

from PIL import Image

import errors

__all__ = (
    "Sprites",
    "Sprite",
    "Layer",
    "sprite"
)

spr = Path("Export_Sprites/")

class Sprites():
    def __init__(self, spriteDict):
        self._dict = spriteDict
        self.body = Layer(self._dict["Dog_body"]["1"])
        self.body2 = Layer(self._dict["Dog_body2"]["1"])
        self.hat = Layer(self._dict["Dog_hat"]["1"])
        self.hair = Layer(self._dict["Dog_hair"]["1"])
        self.expression = Layer(self._dict["Dog_expression"]["1"])

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
        return Layer(self._dict[key])

    def get_layers(self):
        return [i for i in self._dict]

    @property
    def layer(self):
        return Layer(self._dict["1"])

class Layer():
    def __init__(self, data):
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

    def __lt__(self, other):
        if isinstance(other, Layer):
            return sorted([self.root, other.root])[0] == other.root
        return False

    def get_frames(self):
        if self.frames:
            return list(range(len(self.frames)))
        else:
            return [i for i in self.named_frames]
    
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
            return root + str(frame)
        else:
            if frame not in self.named_frames:
                raise errors.FrameNotFound(frame)
            return root + str(self.named_frames[frame])

    def get_frame_path(self, frame, anim=None):
        return spr / (self.get_frame(frame, anim) + ".png")

    async def load_frame(self, frame, anim=None, resize: tuple=False):
        path = self.get_frame_path(frame, anim)
        if path.exists():
            im = Image.open(path)
        else:
            try: # Chicory_lagoon_layer4_smile_9.png does not exist.
                im = Image.open(self.get_frame_path(int(frame) - 1, anim))
            except (FileNotFoundError, ValueError):
                return Image.open(self.get_frame_path(frame))
        if resize:
            im = im.resize(resize)
        return im

with open("sprites.json") as f:
    sprites = Sprites(json.load(f))
