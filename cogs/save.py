import json
import asyncio
import shutil
import logging
import tempfile
import zipfile
from io import BytesIO
from zlib import decompress
from base64 import b64decode

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageChops

from chicorobot import autocomplete
from chicorobot import errors
from chicorobot.assets import *
from chicorobot.sprites import *
from chicorobot.utils import *

async def setup(bot):
    await bot.add_cog(SaveCog(bot))

PAINT_SIZE = (162,91)
PAINT_SIZE_ART = (82, 82)

class Paint():
    def __init__(self, paintdata, not_screen=False):
        if isinstance(paintdata, str):
            paintdata = b64decode(paintdata)
        paintdata = decompress(paintdata).hex()
        self.size = PAINT_SIZE if not not_screen else PAINT_SIZE_ART
        self.paintdata = [[]]
        i = 0
        for i in range(0, len(paintdata), 2 if not_screen else 1):
            if not_screen:
                self.paintdata[-1].append(paintdata[i:i+2])
            else:
                self.paintdata[-1].append(paintdata[i])
            if ((i/2 if not_screen else i)+1) % self.size[0] == 0:
                self.paintdata.append([])
        self.paintdata.remove([])
    
    def __getitem__(self, i):
        if (not isinstance(i, tuple)) or len(i) != 2:
            raise IndexError("Paint getter must be two values, e.g paint[x,y]")
        x, y = i
        if 0 > x >= self.size[0]:
            raise IndexError(f"x value must be between 0 and {self.size[0]-1}")
        if 0 > y >= self.size[1]:
            raise IndexError(f"y value must be between 0 and {self.size[1]-1}")
        return self.paintdata[y][x]

    def iter(self):
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                yield x, y, self.paintdata[y][x]


class SaveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.saves = Path("userdata/saves/")
        if not self.saves.exists():
            self.saves.mkdir()
        # self.screens = Path("chicory-level-screenshots/level_screenshots/")
        # if not self.screens.exists():
        #     logging.warn("Level screenshots not found, can be downloaded with `git submodules update --init`")
        level_datafp = Path("data/level_data")
        if level_datafp.exists():
            with level_datafp.open() as f:
                self.level_data = json.load(f)
        else:
            logging.warn("data/level_data not found.")

    save = app_commands.Group(name="save", description="Commands to do with viewing save info.")

    @save.command(name="upload", description="Upload your save data to be used with other /save subcommands.")
    async def upload(self, interaction: discord.Interaction, playdata: discord.Attachment=None):
        if not playdata:
            await interaction.response.send_message("Your playdata can be found at:\nWindows: `%localappdata%\\paintdog\\save\\`\nMac: `~/Library/Application Support/com.greglobanov.chicory/save/` (in finder user Go > Go to folder)")
        else:
            await interaction.response.defer(thinking=True)
            if playdata.size > 10000000: # 10mb max
                return await interaction.response.send_message("Playdata too large.")
            await playdata.save(self.saves / f"{interaction.user.id}_playdata")
            await interaction.followup.send("Save data uploaded.")

    def get_playdata(self, user):
        savefp = self.saves / f"{user.id}_playdata"
        if not savefp.exists():
            raise errors.SaveNotUploaded()
        with savefp.open() as f:
            save = [i.strip() for i in f.readlines()]
        save[3] = json.loads(save[3])
        save[9] = json.loads(save[9])
        save[18] = json.loads(save[18])
        return save

    @save.command(name="dog", description="Creates the dog from your uploaded savedata.")
    @app_commands.autocomplete(
        expression=autocomplete.expression, hat2=autocomplete.hat, animation=autocomplete.animation
    )
    async def dog(self, interaction: discord.Interaction, expression: str=None, hat2: str="None", animation: str="idle", animated: bool=False, custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None):
        dog = self.bot.get_cog("DogCog")
        save = self.get_playdata(interaction.user)
        if not expression:
            expression = save[3]["expression"] or "normal"
        clothes = save[3]["clothes"]
        if clothes in in_game_clothes: clothes = in_game_clothes[clothes]
        hat = save[3]["hat"]
        if hat in in_game_hats: hat = in_game_hats[hat]
        hair = save[3]["hair"]
        hat_col = from_bgr_decimal(save[3]["color_part_0"])
        body_col = from_bgr_decimal(save[3]["color_part_1"])
        clothes_col = from_bgr_decimal(save[3]["color_part_2"])
        await dog.make_dog(interaction, expression, clothes, hat, hair, hat2, animation, animated, body_col, clothes_col, hat_col, custom_clothes, custom_hat)

    def get_palette(self, screen, save):
        palette = self.level_data[screen]["palette"]
        palette = [(i[0], i[1], i[2]) for i in palettes[palette]] + [from_bgr_decimal(save[3][f"custompaint_{i}"]) for i in range(8) if f"custompaint_{i}" in save[3]]
        palette = {hex(i+1)[-1]: c for i, c in enumerate(palette)}
        palette["0"] = (255, 255, 255)
        if screen == "0_1_0": # pickle
            palette["f"] = (242, 0, 131)
        if screen == "1_0_0": # dust
            palette["f"] = (217, 199, 190)
        return palette

    async def draw_paint(self, paint, palette, not_screen=False):
        paint = Paint(paint, not_screen)
        im = Image.new("RGB", size=paint.size)
        for x, y, col in paint.iter():
            im.putpixel((x,y), palette[col])
        return im

    @save.command(name="screen", description="Shows the paint on a screen in your savedata")
    async def screen(self, interaction: discord.Interaction, screen_layer: str, screen_x: str, screen_y: str):
        await interaction.response.defer(thinking=True)
        screen = f"{screen_layer}_{screen_x}_{screen_y}"
        save = self.get_playdata(interaction.user)
        im = await self.draw_paint(save[18][f"{screen}.paint"], self.get_palette(screen, save))
        im = im.resize((im.size[0]*8, im.size[1]*8), resample=0)
        out = BytesIO()
        im.save(out, format="PNG")
        out.seek(0)
        file = discord.File(out, filename=f"{screen}.png")
        await interaction.followup.send(f"`{screen}`:", file=file)

    @save.command(name="timelapse", description="Makes a timelapse of a given screen file.")
    @app_commands.describe(screen="timelapse file saved by the game in `savefolder/timelapse/` - Can be a class")
    async def timelapse(self, interaction: discord.Interaction, screen: discord.Attachment, loop: bool=False):
        await interaction.response.defer(thinking=True)
        save = self.get_playdata(interaction.user)
        screen_name = screen.filename
        not_screen = "_" not in screen_name
        if screen.size > 10000000:
            return await interaction.followup.send("Timelapse file too large")
        timelapsebytes = BytesIO()
        await screen.save(timelapsebytes)
        timelapsebytes.seek(0)
        if not_screen:
            palette = {}
            cols = save[3]["timelapse_data"][screen_name]["c"]
            palette["00"] = (255, 255, 255)
            for i in range(1, 25):
                h = hex(i)[2:]
                if len(h) == 1: h = "0" + h
                palette[h] = from_bgr_decimal(cols[i-1])
            for i in range(25, 33):
                h = hex(i)[2:]
                if len(h) == 1: h = "0" + h
                if f"custompaint_{i-25}" not in save[3]:
                    break
                palette[h] = from_bgr_decimal(save[3][f"custompaint_{i-25}"])
        else:
            palette = self.get_palette(screen_name, save)
        temp = tempfile.mkdtemp()
        temp = Path(temp)
        print(f"Making temp: {str(temp)}")
        def del_temp():
            if temp:
                try:
                    shutil.rmtree(temp)
                except PermissionError:
                    print("Failed to delete file.")
                else:
                    print(f"Deleted temp: {str(temp)}")
        for i, point in enumerate(save[3]["timelapse_data"][screen_name]["p"]):
            if len(save[3]["timelapse_data"][screen_name]["p"]) != i+1:
                size = int(save[3]["timelapse_data"][screen_name]["p"][i+1] - point)
                timelapsepaint = timelapsebytes.read(size)
            else:
                timelapsepaint = timelapsebytes.read()
            im = await self.draw_paint(timelapsepaint, palette, not_screen)
            im = im.resize((im.size[0]*8, im.size[1]*8), resample=0)
            im.save(temp / f"{i:03}.gif")
        process = await asyncio.create_subprocess_shell(
            f"{gifsicle} --delay 12 --disposal bg {'--loopcount' if loop else '--no-loopcount'} {temp / '*.gif'}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0: # Error
            f = BytesIO()
            with zipfile.ZipFile(f, "x") as zipf:
                for i in temp.glob("*.gif"):
                    zipf.write(i, i.relative_to(temp))
            f.seek(0)
            file = discord.File(f, f"{screen_name}.zip")
            gif_fail = " gif conversion failed"
        else:
            gifdata = BytesIO(stdout)
            file = discord.File(gifdata, f"{screen_name}.gif")
            gif_fail = ""
        await interaction.followup.send(f"`{screen_name}`{gif_fail}:", file=file)
        file.close()
        del_temp()
