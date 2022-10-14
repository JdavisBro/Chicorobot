class SpriteNotFound(Exception):
    def __init__(self, sprite):
        self.sprite = sprite

class LayerNotFound(Exception):
    def __init__(self, layer):
        self.layer = layer

class FrameNotFound(Exception):
    def __init__(self, frame):
        self.frame = frame

class AnimationNotFound(Exception):
    def __init__(self, animation):
        self.animation = animation

class ColourError(Exception):
    pass

class InvalidFrame(Exception):
    pass
