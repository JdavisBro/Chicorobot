import sys
import shutil
from pathlib import Path
from typing import Union

__all__ = (
    "gifsicle",
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

def to_titlecase(string):
    if "-" in string:
        return "-".join([word[0].upper() + word[1:].lower() for word in string.split("-")]) # Half-Moons
    else:
        return " ".join([word[0].upper() + word[1:].lower() for word in string.split(" ")])

def from_bgr_decimal(c):
    c = int(c)
    return ((c >> 0) & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff)
