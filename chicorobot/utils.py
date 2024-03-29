import sys
import shutil
from pathlib import Path
from typing import Union

__all__ = (
    "gifsicle",
    "imagemagick",
    "to_titlecase",
    "from_bgr_decimal"
)

# Check for gifsicle
gifsicle: Union[Path, str, None] = None
gifsicle = shutil.which("gifsicle")
if not gifsicle:
    gifsicle = Path("gifsicle/gifsicle.exe")
    if not gifsicle.exists():
        gifsicle = None

# Check for imagemagick
imagemagick: Union[Path, str, None] = None
if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
    imagemagick = shutil.which("magick")
else:
    imagemagick = shutil.which("convert")
if not imagemagick:
    imagemagick = Path("imagemagick/convert.exe")
    if not imagemagick.exists():
        imagemagick = None

def to_titlecase(string):
    if "-" in string:
        return "-".join([word[0].upper() + word[1:].lower() for word in string.split("-")]) # Half-Moons
    else:
        return " ".join([word[0].upper() + word[1:].lower() for word in string.split(" ")])

def from_bgr_decimal(c):
    c = int(c)
    return ((c >> 0) & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff)
