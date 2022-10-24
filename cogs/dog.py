import asyncio
import random
import tempfile
import shutil
from math import cos, sin
from io import BytesIO
from pathlib import Path

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
    await bot.add_cog(DogCog(bot))

class DogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cclothes = Path("userdata/custom_clothes/")
        if not self.cclothes.exists():
            self.cclothes.mkdir()
        self.chat = Path("userdata/custom_hat/")
        if not self.chat.exists():
            self.chat.mkdir()

    @app_commands.command(name="set_customs", description="Set the custom clothing and/or hat /dog should default to when none are given.")
    async def set_customs(self, interaction: discord.Interaction, clothes: discord.Attachment=None, hat: discord.Attachment=None):
        await interaction.response.defer(thinking=True)
        if clothes:
            im2 = BytesIO()
            if clothes.size > 10000000: # 10mb max
                return await interaction.response.send_message("Clothes image too large (10mb max).")
            await clothes.save(im2)
            im2 = Image.open(im2, formats=["PNG"])
            custom_clothes = Image.new("RGBA", (750, 750), (0,0,0,0))
            custom_clothes.paste(im2, box=(255,424))
            custom_clothes.save(self.cclothes / f"{interaction.user.id}.png")
        if hat:
            im2 = BytesIO()
            if hat.size > 10000000: # 10mb max
                return await interaction.response.send_message("Hat image too large (10mb max)" + (" but custom clothes were set." if clothes else '.'))
            await hat.save(im2)
            im2 = Image.open(im2, formats=["PNG"])
            custom_hat = Image.new("RGBA", (750, 750), (0,0,0,0))
            custom_hat.paste(im2,box=(161,48))
            custom_hat.save(self.chat / f"{interaction.user.id}.png")
        out = "Set custom clothes and custom hat." if clothes and hat else "Set custom clothes." if clothes else "Set custom hat." if hat else "Set nothing." # Lol, lmao.
        await interaction.followup.send(out)

    # Actually makes the dog images
    async def make_dog_image(
        self, expression, clothes, hat, hair, hat2,
        animation, frame,
        body_col, clothes_col, hat_col,
        custom_clothes, custom_hat
    ):
        animation_name = animation.lower()

        if animation_name == "idle":
            base_size = (750, 750)
            to_scaled = 1
        else:
            base_size = (150, 150)
            to_scaled = 5

        if animation_name not in dog_animations:
            raise errors.AnimationNotFound(animation_name)
        animation = dog_animations[animation_name]
        dog_a = animation["A"][3:]
        dog_b = animation["B"][3:]
        dog_ear = animation["ear"][3:]
        anim_origin = animation["origin"]

        body_frame = frame
        if len(animation["frames_body"]) <= frame:
            body_frame = len(animation["frames_body"]) - 1
        
        body_origin = (375, 599)
        
        nobody = False
        
        if animation["frames_body"]:
            body_ang = -animation["frames_body"][body_frame]["ang"]
            body_x = (anim_origin[0]*to_scaled - body_origin[0]) + (animation["frames_body"][body_frame]["x"]*5)
            body_y = (anim_origin[1]*to_scaled - body_origin[1]) + (animation["frames_body"][body_frame]["y"]*5)
        else:
            nobody = True

        head_frame = frame
        if len(animation["frames_head"]) <= frame:
            head_frame = len(animation["frames_head"]) - 1

        head_origin = (225, 370)
        head_ang = animation["frames_head"][head_frame]["ang"]
        head_x = (anim_origin[0]*to_scaled - head_origin[0]) + (animation["frames_head"][head_frame]["x"]*5)
        head_y = (anim_origin[1]*to_scaled - head_origin[1]) + (animation["frames_head"][head_frame]["y"]*5)
        hat_origin = (385, 420)
        hat_x = (anim_origin[0]*to_scaled - hat_origin[0]) + (animation["frames_head"][head_frame]["x"]*5)
        hat_y = (anim_origin[1]*to_scaled - hat_origin[1]) + (animation["frames_head"][head_frame]["y"]*5)

        # -- Animation _B -- #
        if dog_b in sprites.sprites(): # BOB do not have a _B
            im = await sprites[dog_b].layer.load_frame(frame, colour=body_col)
        else:
            im2 = await sprites[dog_ear].layer.load_frame(frame)
            im = Image.new("RGBA", im2.size, (0,0,0,0))

        if not nobody:
            if clothes != "Custom":
                # -- Clothing -- #
                if not sprites.body.is_frame(clothes):
                    raise errors.ClothingNotFound(clothes)
                im2 = await sprites.body.load_frame(clothes, colour=clothes_col)
                im2 = im2.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
                im.alpha_composite(im2)
            else:
                # -- Custom Clothing -- #
                im2 = custom_clothes.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
                im2 = await colour_image(im2, clothes_col)
                im.alpha_composite(im2)

        # -- Clothing _0 -- #
        if sprites.body2.is_frame(clothes+"_0") and not nobody:
            im2 = await sprites.body2.load_frame(clothes + "_0", colour=hat_col)
            im2 = im2.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
            im.alpha_composite(im2)

        # -- Animation _A -- #
        if dog_a in sprites.sprites(): # Some animations do not have an _A
            im2 = await sprites[dog_a].layer.load_frame(frame, colour=body_col)
            im.alpha_composite(im2)

        # -- Clothing _1 -- #
        if sprites.body2.is_frame(clothes+"_1") and not nobody:
            im2 = await sprites.body2.load_frame(clothes+"_1", colour=hat_col)
            im2 = im2.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
            im.alpha_composite(im2)
        
        # -- Neck Hats -- #
        if not nobody:
            for h in [hat,hat2]:
                if h in extraHats:
                    im2 = await sprites.body2.load_frame(h+"_1", colour=hat_col)
                    im2 = im2.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
                    im.alpha_composite(im2)

        # -- Expression -- #
        if expression != "normal":
            fn = Path("expressions/") / (expression + ".png")
            if not fn.exists():
                if expression in expressions_alts:
                    fn = Path("expressions/") / (expressions_alts[expression] + ".png")
                else:
                    raise errors.ExpressionNotFound(expression)
            im3 = Image.open(fn)
            im3 = await colour_image(im3, body_col)
        else:
            im3 = await sprites.head.load_frame(0, colour=body_col)
        im2 = Image.new("RGBA", (750, 750))
        im2.paste(im3)
        im2 = im2.rotate(angle=head_ang, center=head_origin, translate=(head_x, head_y)).resize(base_size)
        im.alpha_composite(im2)    

        # -- Clothing _2 -- #
        if sprites.body2.is_frame(clothes+"_2") and not nobody:
            im2 = await sprites.body2.load_frame(clothes+"_2", colour=clothes_col)
            im2 = im2.rotate(angle=body_ang, center=body_origin, translate=(body_x, body_y)).resize(base_size)
            im.alpha_composite(im2)
        
        # -- Hats _1 -- #
        for h in [hat,hat2]:
            if sprites.hat.is_frame(h+"_1"): # Behind hair part of hat (only used for horns)
                im2 = await sprites.hat.load_frame(h+"_1", colour=hat_col)
                im2 = im2.rotate(angle=head_ang, center=hat_origin, translate=(hat_x, hat_y)).resize(base_size)
                im.alpha_composite(im2)

        # -- Hair -- #
        if all([h in hairHats for h in [hat,hat2]]): # Neither hat doesn't show hair
            if not sprites.hair.is_frame(hair):
                raise errors.HairNotFound(hair)
            im2 = await sprites.hair.load_frame(hair, colour=body_col)
            im2 = im2.rotate(angle=head_ang, center=hat_origin, translate=(hat_x, hat_y)).resize(base_size)
            im.alpha_composite(im2)

        # -- Hat -- #
        async def do_hat():
            for h in [hat, hat2]:
                if h == "None" or h in extraHats:
                    continue
                if h != "Custom":
                    im2 = await sprites.hat.load_frame(h, colour=hat_col)
                    im2 = im2.rotate(angle=head_ang, center=hat_origin, translate=(hat_x, hat_y)).resize(base_size)
                    im.alpha_composite(im2)
                else:
                    im2 = custom_hat.rotate(angle=head_ang, center=hat_origin, translate=(hat_x, hat_y)).resize(base_size) # MIGHT NOT WORK MAKE SURE TO TEST :D
                    im.alpha_composite(await colour_image(im2, hat_col))

        async def do_ear():
            im2 = await sprites[dog_ear].layer.load_frame(frame, colour=body_col)
            im.alpha_composite(im2)

        for h in [hat, hat2]:
            if h == "None" or h == "Custom" or h in extraHats:
                continue
            if not sprites.hat.is_frame(h):
                raise errors.HatNotFound(h)

        if any([h in hatOverEar for h in [hat,hat2]]):
            await do_ear()
            await do_hat()
        else:
            await do_hat()
            await do_ear()

        # -- TRANSIT PASS -- #
        if animation_name == "transit":
            im3 = Image.new("RGBA", (base_size[0], base_size[1] + 38), (0,0,0,0))
            im3.paste(im, (0, 38))
            im = im3
            im2 = await sprites["Dog_transit_card"].layer.load_frame(frame)
            im.alpha_composite(im2)

        return im

    # Function that creates and sends dogs, used by dog and random_dog
    async def make_dog(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            animation: str="idle", animated: bool=False,
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
            extra_text: str=""
        ):
        await interaction.response.defer(thinking=True)

        clothes = to_titlecase(clothes)
        hat = to_titlecase(hat)
        hat2 = to_titlecase(hat2)

        expression = expression.lower()

        animation = animation.lower()

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
        if not animated:
            im = await self.make_dog_image(expression, clothes, hat, hair, hat2, animation, 0, body_col, clothes_col, hat_col, custom_clothes, custom_hat)
            imbyte = BytesIO()
            im.save(imbyte, "PNG")
            imbyte.seek(0)
            file = discord.File(imbyte, "dog.png")
        else:
            if animation not in dog_animations:
                return await interaction.followup.send("Animation not found :(")
            if dog_animations[animation]["A"][3:] in sprites.sprites():
                frames = sprites[dog_animations[animation]["A"][3:]].layer.get_frames()
            elif dog_animations[animation]["B"][3:] in sprites.sprites():
                frames = sprites[dog_animations[animation]["B"][3:]].layer.get_frames()
            elif dog_animations[animation]["ear"][3:] in sprites.sprites():
                frames = sprites[dog_animations[animation]["ear"][3:]].layer.get_frames()
            else:
                return await interaction.followup.send("Animation not found :(")
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
            for frame in frames:
                im = await self.make_dog_image(expression, clothes, hat, hair, hat2, animation, frame, body_col, clothes_col, hat_col, custom_clothes, custom_hat)
                im.save(temp / f"{frame:03}.png")
            process = await asyncio.create_subprocess_shell(
                f"{imagemagick} -delay 1x8 -loop 0 -dispose Background {temp / '*.png'} {temp / 'out.gif'}", # honestly not sure on the FPS or what the `speed` variable means
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode != 0: # Error
                print(f"GIF CONVERSION ERROR: {await process.stdout.read()}")
                return await interaction.followup.send(content="Animation Error.")
            file = discord.File(temp / "out.gif", f"Dog.gif")
        await interaction.followup.send(content=f"Dog:\n`/dog expression:{expression} clothes:{clothes} hat:{hat} hair:{hair} hat2:{hat2} animation:{animation} animated:{animated} body_col:{('#%02x%02x%02x' % body_col) if isinstance(body_col, tuple) else body_col} clothes_col:{('#%02x%02x%02x' % clothes_col) if isinstance(clothes_col, tuple) else clothes_col} hat_col:{('#%02x%02x%02x' % hat_col) if isinstance(hat_col, tuple) else hat_col}`{extra_text}", file=file)
        file.close()
        del_temp()

    @app_commands.command(name="random_dog", description="Make a random dog!")
    @app_commands.describe(use_in_game_colors="Only use colours from the game. Default: True", use_palette="Specify palette to be used, can be None or Random. Default: None" , add_hat2="Add a random hat2. Default: False", animated="Make dog animated. Default: False", random_animation="Randomize Animation. Default: False")
    @app_commands.autocomplete(use_palette=autocomplete.random_palette)
    async def random_dog(self, interaction: discord.Interaction, use_in_game_colors: bool=True, use_palette: str="None", add_hat2: bool=False, animated: bool=False, random_animation: bool=False):
        global colour_image
        active = False
        if random.randint(0,1000) == 0 and Path("gay.png").exists():
            import chicorobot.sprites
            active = True
            old = colour_image
            gayim = Image.open("gay.png").convert("RGBA")
            async def gay_mode(im, colour): 
                return ImageChops.multiply(im, gayim.resize(im.size)) # HI IF YOU SEE THIS PLEASE KEEP IT A SECRET (pretyt please)
            chicorobot.sprites.colour_image = gay_mode # also what the fuck WHAT THE FUCK this should be illegal
            colour_image = chicorobot.sprites.colour_image
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
        await self.make_dog(
            interaction,
            random.choice(["normal"] + [i.stem for i in Path("expressions/").iterdir()]),
            random.choice(sprites["Dog_body"].layer.get_frames()),
            random.choice([i for i in sprites["Dog_hat"].layer.get_frames() if i != "Horns_1"] + ["None"] + extraHats),
            random.choice(sprites["Dog_hair"].layer.get_frames()),
            "None" if not add_hat2 else random.choice(sprites["Dog_hat"].layer.get_frames() + ["None"] + extraHats),
            "idle" if not random_animation else random.choice(list(dog_animations.keys())),
            animated,
            colone,
            coltwo,
            colthree,
            extra_text=f"\nPalette: {chosen}" + (" - 1/1001 CHANCE!! GAY MODE IS ACTIVE!!" if active else "") # shhh keep it secret please
        )
        if active:
            chicorobot.sprites.colour_image = old



    @app_commands.command(name="dog", description="Make a Dog!")
    @app_commands.autocomplete(
        expression=autocomplete.expression, clothes=autocomplete.clothes,
        hat=autocomplete.hat, hat2=autocomplete.hat, hair=autocomplete.hair,
        animation=autocomplete.animation
    )
    async def dog(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            animation: str="idle", animated: bool= False,
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None
        ):
        await self.make_dog(interaction, expression, clothes, hat, hair, hat2, animation, animated, body_col, clothes_col, hat_col, custom_clothes, custom_hat)