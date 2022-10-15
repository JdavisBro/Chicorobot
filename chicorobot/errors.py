class SpriteNotFound(Exception):
    def __init__(self, sprite):
        self.sprite = sprite

class LayerNotFound(Exception):
    def __init__(self, layer):
        self.layer = layer

class FrameNotFound(Exception):
    def __init__(self, frame):
        self.frame = frame

class ClothingNotFound(Exception):
    def __init__(self, clothing):
        self.clothing = clothing

class HatNotFound(Exception):
    def __init__(self, hat):
        self.hat = hat

class HairNotFound(Exception):
    def __init__(self, hair):
        self.hair = hair

class ExpressionNotFound(Exception):
    def __init__(self, expression):
        self.expression = expression

class AnimationNotFound(Exception):
    def __init__(self, animation):
        self.animation = animation

class ColourError(Exception):
    pass

class InvalidFrame(Exception):
    pass
