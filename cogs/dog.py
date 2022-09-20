import random
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

from chicorobot import autocomplete
from chicorobot.assets import *
from chicorobot.sprites import *
from chicorobot.utils import to_titlecase

async def setup(bot):
    await bot.add_cog(DogCog(bot))

class DogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function that creates and sends dogs, used by dog and random_dog
    async def make_dog(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
            extra_text: str=""
        ):
        await interaction.response.defer(thinking=True)

        clothes = to_titlecase(clothes)
        hat = to_titlecase(hat)
        hat2 = to_titlecase(hat2)

        expression = expression.lower()

        base_size = (750, 750)

        # -- Animation _B -- #
        im = await sprites["Dog_idle_B"].layer.load_frame(0, resize=base_size, colour=body_col)

        if clothes != "Custom":
            # -- Clothing -- #
            if not sprites.body.is_frame(clothes):
                await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{clothes}` is not a clothing!")
                return
            im2 = await sprites.body.load_frame(clothes, resize=base_size, colour=clothes_col) # Clothes
            im.alpha_composite(im2)
        else:
            # -- Custom Clothing -- #
            if not custom_clothes:
                await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply custom clothes!")
                return
            im2 = BytesIO()
            await custom_clothes.save(im2)
            im2 = Image.open(im2, formats=["PNG"])
            im3 = Image.new("RGBA", im.size, (0,0,0,0))
            im3.paste(im2,box=(220,433),mask=im2)
            im3 = await colour_image(im3, clothes_col)
            im.alpha_composite(im3)

        # -- Clothing _0 -- #
        if sprites.body2.is_frame(clothes+"_0"):
            im2 = await sprites.body2.load_frame(clothes + "_0", resize=base_size, colour=hat_col)
            im.alpha_composite(im2)

        # -- Animation _A -- #
        im2 = await sprites["Dog_idle_A"].layer.load_frame(0, resize=base_size, colour=body_col)
        im.alpha_composite(im2)

        # -- Clothing _1 -- #
        if sprites.body2.is_frame(clothes+"_1"):
            im2 = await sprites.body2.load_frame(clothes+"_1", resize=base_size, colour=hat_col)
            im.alpha_composite(im2)
        
        # -- Neck Hats -- #
        for h in [hat,hat2]:
            if h in extraHats:
                im2 = await sprites.body2.load_frame(h+"_1", resize=base_size, colour=hat_col)
                im.alpha_composite(im2)

        # -- Expression -- #
        if expression != "normal":
            if not sprites.expression.is_frame(expression):
                await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{expression}` is not an expression!")
                return
            im2 = await sprites.expression.load_frame(expression, resize=base_size, colour=body_col)
        else:
            im3 = await sprites.head.load_frame(0, colour=body_col)
            im2 = Image.new("RGBA", base_size)
            im2.paste(im3, box=(150, 50))
        im.alpha_composite(im2)    

        # -- Clothing _2 -- #
        if sprites.body2.is_frame(clothes+"_2"):
            im2 = await sprites.body2.load_frame(clothes+"_2", resize=base_size, colour=clothes_col)
            im.alpha_composite(im2)
        
        # -- Hats _1 -- #
        for h in [hat,hat2]:
            if sprites.hat.is_frame(h+"_1"): # Behind hair part of hat (only used for horns)
                im2 = await sprites.hat.load_frame(h+"_1", resize=base_size, colour=hat_col)
                im.alpha_composite(im2)

        # -- Hair -- #
        if all([h in hairHats for h in [hat,hat2]]): # Neither hat doesn't show hair
            if not sprites.hair.is_frame(hair):
                await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{hair}` is not a hair!")
                return
            im2 = await sprites.hair.load_frame(hair, resize=base_size, colour=body_col)
            im.alpha_composite(im2)

        # -- Hat -- #
        async def do_hat():
            for h in [hat, hat2]:
                if h == "None" or h in extraHats:
                    continue
                if h != "Custom":
                    im2 = await sprites.hat.load_frame(h, resize=base_size, colour=hat_col)
                    im.alpha_composite(im2)
                else:
                    if not custom_hat:
                        await interaction.followup.send(content="<:Pizza_Cease:967483853910462536> You didn't supply a custom hat!")
                        return
                    im2 = BytesIO()
                    await custom_hat.save(im2)
                    im2 = Image.open(im2, formats=["PNG"])
                    im3 = Image.new("RGBA", im.size, (0,0,0,0))
                    im3.paste(im2,box=(129,45),mask=im2)
                    im.alpha_composite(await colour_image(im3, hat_col))

        async def do_ear():
            im2 = await sprites["Dog_idle_ear"].layer.load_frame(0, resize=base_size, colour=body_col)
            im.alpha_composite(im2)

        for h in [hat, hat2]:
            if h == "None" or h == "Custom" or h in extraHats:
                continue
            if not sprites.hat.is_frame(h):
                await interaction.followup.send(f"<:Pizza_OhGod:967483357388759070> `{h}` is not a hat!")
                return

        if any([h in hatOverEar for h in [hat,hat2]]):
            await do_ear()
            await do_hat()
        else:
            await do_hat()
            await do_ear()

        imbyte = BytesIO()
        im.save(imbyte, "PNG")
        imbyte.seek(0)
        file = discord.File(imbyte, "dog.png")
        await interaction.followup.send(content=f"Dog:\n`/dog expression:{expression} clothes:{clothes} hat:{hat} hair:{hair} hat2:{hat2} body_col:{('#%02x%02x%02x' % body_col) if isinstance(body_col, tuple) else body_col} clothes_col:{('#%02x%02x%02x' % clothes_col) if isinstance(clothes_col, tuple) else clothes_col} hat_col:{('#%02x%02x%02x' % hat_col) if isinstance(hat_col, tuple) else hat_col}`{extra_text}", file=file)

    @app_commands.command(name="random_dog", description="Make a random dog!")
    @app_commands.describe(use_palettes="Only use colours from the game. Default: True", limit_to_one_palette="Choose one palette from the game and use colours from it. Default: False", palette="Specify palette to be used with limit_to_one_palette. Default: Random" , add_hat2="Add a random hat2. Default: False")
    @app_commands.autocomplete(palette=autocomplete.area_name)
    async def random_dog(self, interaction: discord.Interaction, use_palettes: bool=True, limit_to_one_palette: bool=False, palette: str=None, add_hat2: bool=False):
        chosen = None
        if use_palettes:
            if limit_to_one_palette: # Single palette limited
                if palette != None and palette.lower() != "random": # Specified palette
                    palette = to_titlecase(palette)

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
        await self.make_dog(
            interaction,
            random.choice(sprites["Dog_expression"].layer.get_frames()),
            random.choice(sprites["Dog_body"].layer.get_frames()),
            random.choice([i for i in sprites["Dog_hat"].layer.get_frames() if i != "Horns_1"] + ["None"] + extraHats),
            random.choice(sprites["Dog_hair"].layer.get_frames()),
            "None" if not add_hat2 else random.choice(sprites["Dog_hat"].layer.get_frames() + ["None"] + extraHats),
            colone,
            coltwo,
            colthree,
            extra_text="" if not limit_to_one_palette else f"\nPalette: {chosen}"
        )

    @app_commands.command(name="dog", description="Make a Dog!")
    @app_commands.autocomplete(
        expression=autocomplete.expression, clothes=autocomplete.clothes,
        hat=autocomplete.hat, hat2=autocomplete.hat, hair=autocomplete.hair
    )
    async def dog(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None
        ):
        await self.make_dog(interaction, expression, clothes, hat, hair, hat2, body_col, clothes_col, hat_col, custom_clothes, custom_hat)