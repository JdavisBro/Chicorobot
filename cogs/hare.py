import asyncio
import random
import tempfile
import shutil
from io import BytesIO
from pathlib import Path

import discord
import numpy
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageChops

from chicorobot import autocomplete
from chicorobot import errors
from chicorobot.assets import *
from chicorobot.sprites import *
from chicorobot.utils import *

# This code is heavily a modified version of dog.py and incredibly hardcoded
# eww

async def setup(bot):
    await bot.add_cog(HareCog(bot))

class RandomRepeatView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=None)
        self.repeat.label = f"Repeat! ({data})"

    @discord.ui.button(label="Repeat! (0)", emoji="🔁", custom_id="randomrepeat:hare")
    async def repeat(self, interaction, button):
        hare = interaction.client.get_cog("HareCog")
        i = button.label.index("(") + 1
        data = int(button.label[i:button.label.index(")",i)])
        use_in_game_colors = bool(data & 0b00001)
        random_palette =     bool(data & 0b00010)
        add_hat2 =           bool(data & 0b00100)
        for cmd in hare.walk_app_commands():
            if cmd.name == "random_hare":
                await cmd.callback(hare, interaction, use_in_game_colors, ("Random" if random_palette else "None"), add_hat2)

class HareCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dog = bot.get_cog("DogCog")
        self.cclothes = self.dog.cclothes
        self.chat = self.dog.chat
        randomview = RandomRepeatView(1)
        if not self.bot.HareRandomRepeatView:
            self.bot.HareRandomRepeatView = randomview
            self.bot.add_view(self.bot.HareRandomRepeatView)
        else:
            self.bot.HareRandomRepeatView = randomview

    # Actually makes the hare images
    async def make_hare_image(
        self, expression, clothes, hat, hair, hat2,
        body_col, clothes_col, hat_col,
        custom_clothes, custom_hat
    ):
        body_x = 50 + 252
        body_y = 50 + 350

        hat_x = 50 + 283
        hat_y = 50 + 390
        hair_x = 50 + 283
        hair_y = 50 + 390
        if "Glasses" in hat or "Shades" in hat or hat == "Horns": # lol dw about this code ignore it
            hat_x -= 7
            hat_y -= 5
            if hat == "Horns":
                hat_y -= 1
        hat_scale = 1
        if hat in ["Beak", "Beard", "Clown", "Stache", "Sparkles", "Mask"]:
            hat_scale = 0.5
            hat_x += 25
            hat_y += 15
            if hat == "Mask":
                hat_y += 10

        if clothes in ["Smock", "Sequins"]:
            clothmask = Image.open("chicorobot/hareClothesMask.png")
        elif clothes in ["Bee", "Hiker"]:
            clothmask = None
        else:
            clothmask = Image.open("chicorobot/hareClothesMaskLess.png")

        # -- Chicory layer 1 -- #
        im2 = await sprites["Chicory_idle"].layer.load_frame(0, colour=clothes_col)
        base_size = im2.size

        buffer_add = 50
        buffer_size = (im2.size[0] + (buffer_add*2), im2.size[1] + (buffer_add*2))
        im = Image.new("RGBA", buffer_size, (0,0,0,0))
        
        def put_image(im2, x=0, y=0):
            pos = [int(x)+buffer_add,int(y)+buffer_add]
            im3 = Image.new("RGBA", buffer_size, (0,0,0,0))
            im3.paste(im2, pos)
            im.alpha_composite(im3)
        
        put_image(im2)
        
        im2 = Image.open("chicorobot/hareBackMask.png")
        put_image(im2)

        def put_resize(im, x, y, resize=base_size, body=False):
            resize = (int(resize[0]), int(resize[1]))
            im = im.transpose(0)
            if body and clothmask:
                im3 = Image.new("RGBA", im.size, (0,0,0,0))
                im3.paste(im, mask=clothmask)
                im = im3
            buffer_scaled = int(buffer_add)
            im2 = Image.new("RGBA", (im.width+buffer_scaled*2, im.height+buffer_scaled*2), (0,0,0,0))
            im2.paste(im, (buffer_scaled, buffer_scaled))
            im = im2
            resize = (resize[0] + buffer_add*2, resize[1] + buffer_add*2)
            if resize != im.size:
                im = im.resize(resize)
            put_image(im, x-buffer_add, y-buffer_add)

        if clothes != "Custom":
            # -- Clothing -- #
            if not sprites.body.is_frame(clothes):
                raise errors.ClothingNotFound(clothes)
            im2 = await sprites.body.load_frame(clothes, colour=clothes_col)
            put_resize(im2, body_x, body_y, resize=(im2.width // 4, im2.height // 4), body=True)
        else:
            # -- Custom Clothing -- #
            im2 = await colour_image(custom_clothes, clothes_col)
            put_resize(im2, body_x, body_y, resize=(im2.width // 4, im2.height // 4), body=True)

        # -- Clothing _0 -- #
        if sprites.body2.is_frame(clothes+"_0"):
            im2 = await sprites.body2.load_frame(clothes + "_0", colour=hat_col)
            put_resize(im2, body_x, body_y, resize=(im2.width // 4, im2.height // 4), body=True)

        im2 = Image.open("chicorobot/hareCapeCover.png")
        im2 = await colour_image(im2, clothes_col)
        put_image(im2)
        
        im2 = await sprites["Chicory_idle"]["2"].load_frame(0, colour=body_col)
        put_image(im2)

        im2 = await sprites["Chicory_idle"]["3"].load_frame(0, colour=clothes_col)
        put_image(im2)

        # -- Clothing _1 -- #
        if sprites.body2.is_frame(clothes+"_1"):
            im2 = await sprites.body2.load_frame(clothes+"_1", colour=hat_col)
            put_resize(im2, body_x, body_y-12, resize=(im2.width // 4, im2.height // 4))
        
        # -- Neck Hats -- #
        for h in [hat,hat2]:
            if h in extraHats:
                im2 = await sprites.body2.load_frame(h+"_1", colour=hat_col)
                put_resize(im2, body_x, body_y-12, resize=(im2.width // 4, im2.height // 4))

        # -- Expression -- #
        if expression == "normal":
            expression = None
        im3 = await sprites["Chicory_ok"]["4"].load_frame(0, colour=body_col, anim=expression)
        put_image(im3)
        
        # -- Hats _1 -- #
        for h in [hat,hat2]:
            if sprites.hat.is_frame(h+"_1"): # Behind hair part of hat (only used for horns)
                im2 = await sprites.hat.load_frame(h+"_1", colour=hat_col)
                put_resize(im2, hat_x+7, hat_y+4, resize=(im2.width // 6 * hat_scale, im2.height // 6 * hat_scale))

        # -- Hair -- #
        if all([h in hairHats for h in [hat,hat2]]): # Neither hat doesn't show hair
            if not sprites.hair.is_frame(hair):
                raise errors.HairNotFound(hair)
            im2 = await sprites.hair.load_frame(hair, colour=body_col)
            put_resize(im2, hair_x, hair_y, resize=(im2.width // 6, im2.height // 6))

        for h in [hat, hat2]:
            if h == "None" or h in extraHats:
                continue
            if h != "Custom":
                if not sprites.hat.is_frame(h):
                    raise errors.HatNotFound(h)
                im2 = await sprites.hat.load_frame(h, colour=hat_col)
            else:
                im2 = await colour_image(custom_hat, hat_col)
            put_resize(im2, hat_x, hat_y, resize=(im2.width // 6 * hat_scale, im2.height // 6 * hat_scale))

        if sprites.body2.is_frame(clothes+"_2"):
            im2 = await sprites.body2.load_frame(clothes+"_2", colour=clothes_col)
            put_resize(im2, body_x, body_y, resize=(im2.width // 4, im2.height // 4))

        imnp = numpy.array(im)
        imnp = numpy.where(imnp[:, :, 3] > 0) # Non transparent pixels
        crop  = [imnp[1].min(), imnp[0].min(), imnp[1].max(), imnp[0].max()]
        
        return im, crop

    # Function that creates and sends hares, used by hare and random_hare
    async def make_hare(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
            extra_text: str="", view=discord.utils.MISSING
        ):
        await interaction.response.defer(thinking=True)

        if "Gay" in extra_text:
            body_col = "gay"
            clothes_col = "gay"
            hat_col = "gay"

        clothes = to_titlecase(clothes)
        hat = to_titlecase(hat)
        hat2 = to_titlecase(hat2)

        expression = expression.lower()

        # animation = animation.lower()

        if clothes == "Custom":
            if not custom_clothes:
                if not (self.cclothes / f"{interaction.user.id}.png").exists():
                    return await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply custom clothes! You can set a default with `/set_customs` or specify with the `custom_clothes` argument.")
                custom_clothes = Image.open(self.cclothes / f"{interaction.user.id}.png")
            else:
                im2 = BytesIO()
                await custom_clothes.save(im2)
                im2 = Image.open(im2, formats=["PNG"])
                custom_clothes = Image.new("RGBA", (750, 750), (0,0,0,0))
                custom_clothes.paste(im2, box=(255,424))

        if hat == "Custom" or hat2 == "Custom":
            if not custom_hat:
                if not (self.chat / f"{interaction.user.id}.png").exists():
                    return await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply a custom hat! You can set a default with `/set_customs` or specify with the `custom_hat` argument.")
                custom_hat = Image.open(self.chat / f"{interaction.user.id}.png")
            else:
                im2 = BytesIO()
                await custom_hat.save(im2)
                im2 = Image.open(im2, formats=["PNG"])
                custom_hat = Image.new("RGBA", (750, 750), (0,0,0,0))
                custom_hat.paste(im2,box=(161,48))

        def del_temp():
            pass
        im, crop = await self.make_hare_image(expression, clothes, hat, hair, hat2, body_col, clothes_col, hat_col, custom_clothes, custom_hat)
        im = im.crop(crop)
        imbyte = BytesIO()
        im.save(imbyte, "PNG")
        imbyte.seek(0)
        file = discord.File(imbyte, "hare.png")
        await interaction.followup.send(content=f"Hare:\n`/hare expression:{expression} clothes:{clothes} hat:{hat} hair:{hair} hat2:{hat2} body_col:{('#%02x%02x%02x' % body_col) if isinstance(body_col, tuple) else body_col} clothes_col:{('#%02x%02x%02x' % clothes_col) if isinstance(clothes_col, tuple) else clothes_col} hat_col:{('#%02x%02x%02x' % hat_col) if isinstance(hat_col, tuple) else hat_col}`{extra_text}", file=file, view=view)
        file.close()
        del_temp()

    @app_commands.command(name="random_hare", description="Make a random hare!")
    @app_commands.describe(use_in_game_colors="Only use colours from the game. Default: True", use_palette="Specify palette to be used, can be None or Random. Default: None" , add_hat2="Add a random hat2. Default: False")
    @app_commands.autocomplete(use_palette=autocomplete.random_palette)
    async def random_hare(self, interaction: discord.Interaction, use_in_game_colors: bool=True, use_palette: str="None", add_hat2: bool=False):
        active = True
        # if random.randint(0,199) == 0:
        #     active = True
        chosen = "None"
        if use_in_game_colors:
            if use_palette.lower() != "none": # Single palette limited
                if use_palette.lower() != "random": # Specified palette
                    palette = to_titlecase(use_palette)

                    if palette in paletteAliases:
                        chosen = paletteAliases[palette]
                    else:
                        return await interaction.response.send("Incorrect palette.")
                else:
                    chosen = random.choice(randomablePalettes)
                cols = palettes[chosen]
            else: # Not single palette limited
                cols = all_colours
            colone = tuple(random.choice(cols))
            coltwo = tuple(random.choice(cols))
            colthree = tuple(random.choice(cols))
        else:
            colone = discord.Colour.random()
            coltwo = discord.Colour.random()
            colthree = discord.Colour.random()
        view = discord.utils.MISSING
        if use_palette in ["Random", "None"]:
            value = (0b00100 * add_hat2) + (0b00010 * (use_palette == "Random")) + (0b00001 * use_in_game_colors)
            view = RandomRepeatView(value)
        await self.make_hare(
            interaction,
            random.choice(["normal"] + [i for i in sprites["Chicory_ok"]["4"].anim_root.keys()]),
            random.choice(sprites["Dog_body"].layer.get_frames()),
            random.choice([i for i in sprites["Dog_hat"].layer.get_frames() if i != "Horns_1"] + ["None"] + extraHats),
            random.choice(sprites["Dog_hair"].layer.get_frames()),
            "None" if not add_hat2 else random.choice(sprites["Dog_hat"].layer.get_frames() + ["None"] + extraHats),
            colone,
            coltwo,
            colthree,
            extra_text=f"\nPalette: {chosen}" + (" - Gay Mode Active, happy gay month." if active else ""),
            view=view
        )

    @app_commands.command(name="hare", description="Make a Hare!")
    @app_commands.autocomplete(
        expression=autocomplete.hare_expression, clothes=autocomplete.clothes,
        hat=autocomplete.hat, hat2=autocomplete.hat, hair=autocomplete.hair,
    )
    async def hare(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None
        ):
        await self.make_hare(interaction, expression, clothes, hat, hair, hat2, body_col, clothes_col, hat_col, custom_clothes, custom_hat)