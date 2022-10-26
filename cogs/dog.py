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

async def setup(bot):
    await bot.add_cog(DogCog(bot))
    bot.RandomRepeatView = RandomRepeatView(1)

class RandomRepeatView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=None)
        self.repeat.label = f"Repeat! ({data})"

    @discord.ui.button(label="Repeat! (0)", emoji="🔁", custom_id="randomrepeat:repeat")
    async def repeat(self, interaction, button):
        dog = interaction.client.get_cog("DogCog")
        i = button.label.index("(") + 1
        data = int(button.label[i:button.label.index(")",i)])
        use_in_game_colors = bool(data & 0b00001)
        random_palette =     bool(data & 0b00010)
        add_hat2 =           bool(data & 0b00100)
        animated =           bool(data & 0b01000)
        random_animation =   bool(data & 0b10000)
        for cmd in dog.walk_app_commands():
            if cmd.name == "random_dog":
                await cmd.callback(dog, interaction, use_in_game_colors, ("Random" if random_palette else "None"), add_hat2, animated, random_animation)

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
            scale = 5
            to_scale = 1
        else:
            base_size = (150, 150)
            scale = 1
            to_scale = 5

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
            body_x = (anim_origin[0] - body_origin[0]//to_scale) + (animation["frames_body"][body_frame]["x"]*scale)
            body_y = (anim_origin[1] - body_origin[1]//to_scale) + (animation["frames_body"][body_frame]["y"]*scale)
        else:
            nobody = True

        head_frame = frame
        if len(animation["frames_head"]) <= frame:
            head_frame = len(animation["frames_head"]) - 1

        head_origin = (225, 370)
        head_ang = animation["frames_head"][head_frame]["ang"]
        head_x = (anim_origin[0] - head_origin[0]//to_scale) + (animation["frames_head"][head_frame]["x"]*scale)
        head_y = (anim_origin[1] - head_origin[1]//to_scale) + (animation["frames_head"][head_frame]["y"]*scale)
        hat_origin = (385, 420)
        hat_x = (anim_origin[0] - hat_origin[0]//to_scale) + (animation["frames_head"][head_frame]["x"]*scale)
        hat_y = (anim_origin[1] - hat_origin[1]//to_scale) + (animation["frames_head"][head_frame]["y"]*scale)

        # -- Animation _B -- #
        if dog_b in sprites.sprites(): # BOB do not have a _B
            im2 = await sprites[dog_b].layer.load_frame(frame, colour=body_col)
        else:
            im2 = await sprites[dog_ear].layer.load_frame(frame)
            im2 = Image.new("RGBA", im2.size, (0,0,0,0))

        buffer_add = 50
        buffer_size = (im2.size[0] + (buffer_add*2), im2.size[1] + (buffer_add*2))
        im = Image.new("RGBA", buffer_size, (0,0,0,0))
        
        def put_image(im2, x=0, y=0):
            pos = [int(x)+buffer_add,int(y)+buffer_add]
            im3 = Image.new("RGBA", buffer_size, (0,0,0,0))
            im3.paste(im2, pos)
            im.alpha_composite(im3)
        
        put_image(im2)

        def put_rotate_resize(im, x, y, degrees, origin, resize=base_size):
            buffer_scaled = int(buffer_add*to_scale)
            origin = (origin[0] + buffer_scaled, origin[1] + buffer_scaled)
            im2 = Image.new("RGBA", (im.width+buffer_scaled*2, im.height+buffer_scaled*2), (0,0,0,0))
            im2.paste(im, (buffer_scaled, buffer_scaled))
            im = im2.rotate(degrees, center=origin)
            resize = (resize[0] + buffer_add*2, resize[1] + buffer_add*2)
            if resize != im.size:
                im = im.resize(resize)
            put_image(im, x-buffer_add, y-buffer_add)

        if not nobody:
            if clothes != "Custom":
                # -- Clothing -- #
                if not sprites.body.is_frame(clothes):
                    raise errors.ClothingNotFound(clothes)
                im2 = await sprites.body.load_frame(clothes, colour=clothes_col)
                put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)
            else:
                # -- Custom Clothing -- #
                im2 = await colour_image(custom_clothes, clothes_col)
                put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)

        # -- Clothing _0 -- #
        if sprites.body2.is_frame(clothes+"_0") and not nobody:
            im2 = await sprites.body2.load_frame(clothes + "_0", colour=hat_col)
            put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)

        # -- Animation _A -- #
        if dog_a in sprites.sprites(): # Some animations do not have an _A
            im2 = await sprites[dog_a].layer.load_frame(frame, colour=body_col)
            put_image(im2)

        # -- Clothing _1 -- #
        if sprites.body2.is_frame(clothes+"_1") and not nobody:
            im2 = await sprites.body2.load_frame(clothes+"_1", colour=hat_col)
            put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)
        
        # -- Neck Hats -- #
        if not nobody:
            for h in [hat,hat2]:
                if h in extraHats:
                    im2 = await sprites.body2.load_frame(h+"_1", colour=hat_col)
                    put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)

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
        put_rotate_resize(im2, head_x, head_y, head_ang, head_origin)

        # -- Clothing _2 -- #
        if sprites.body2.is_frame(clothes+"_2") and not nobody:
            im2 = await sprites.body2.load_frame(clothes+"_2", colour=clothes_col)
            put_rotate_resize(im2, body_x, body_y, body_ang, body_origin)
        
        # -- Hats _1 -- #
        for h in [hat,hat2]:
            if sprites.hat.is_frame(h+"_1"): # Behind hair part of hat (only used for horns)
                im2 = await sprites.hat.load_frame(h+"_1", colour=hat_col)
                put_rotate_resize(im2, hat_x, hat_y, head_ang, hat_origin)

        # -- Hair -- #
        if all([h in hairHats for h in [hat,hat2]]): # Neither hat doesn't show hair
            if not sprites.hair.is_frame(hair):
                raise errors.HairNotFound(hair)
            im2 = await sprites.hair.load_frame(hair, colour=body_col)
            put_rotate_resize(im2, hat_x, hat_y, head_ang, hat_origin)

        # -- Hat -- #
        async def do_hat():
            for h in [hat, hat2]:
                if h == "None" or h in extraHats:
                    continue
                if h != "Custom":
                    im2 = await sprites.hat.load_frame(h, colour=hat_col)
                else:
                    im2 = custom_hat
                put_rotate_resize(im2, hat_x, hat_y, head_ang, hat_origin)

        async def do_ear():
            im2 = await sprites[dog_ear].layer.load_frame(frame, colour=body_col)
            put_image(im2)

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
            im2 = await sprites["Dog_transit_card"].layer.load_frame(frame)
            put_image(im2, 0, -38)

        imnp = numpy.array(im)
        imnp = numpy.where(imnp[:, :, 3] > 0) # Non transparent pixels
        crop  = [imnp[1].min(), imnp[0].min(), imnp[1].max(), imnp[0].max()]
        
        return im, crop

    # Function that creates and sends dogs, used by dog and random_dog
    async def make_dog(
            self, interaction: discord.Interaction,
            expression: str, clothes: str, hat: str, hair: str="Simple", hat2: str="None",
            animation: str="idle", animated: bool=False,
            body_col: str="#ffffff", clothes_col: str="#ffffff", hat_col: str="#ffffff",
            custom_clothes: discord.Attachment=None, custom_hat: discord.Attachment=None,
            extra_text: str="", view=discord.utils.MISSING
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
            im, crop = await self.make_dog_image(expression, clothes, hat, hair, hat2, animation, 0, body_col, clothes_col, hat_col, custom_clothes, custom_hat)
            im = im.crop(crop)
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
            cropfull = None
            for frame in frames:
                im, crop = await self.make_dog_image(expression, clothes, hat, hair, hat2, animation, frame, body_col, clothes_col, hat_col, custom_clothes, custom_hat)
                if not cropfull:
                    cropfull = crop
                else:
                    cropfull[0] = min(crop[0], cropfull[0])
                    cropfull[1] = min(crop[1], cropfull[1])
                    cropfull[2] = max(crop[2], cropfull[2])
                    cropfull[3] = max(crop[3], cropfull[3])
                im.save(temp / f"{frame:03}.png")
            addcrop = f"-crop {cropfull[2]-cropfull[0]}x{cropfull[3]-cropfull[1]}+{cropfull[0]}+{cropfull[1]} +repage "
            process = await asyncio.create_subprocess_shell(
                f"{imagemagick} -delay 1x8 -loop 0 -dispose Background {addcrop}{temp / '*.png'} {temp / 'out.gif'}", # honestly not sure on the FPS or what the `speed` variable means
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode != 0: # Error
                print(f"GIF CONVERSION ERROR: {await process.stdout.read()}")
                return await interaction.followup.send(content="Animation Error.")
            file = discord.File(temp / "out.gif", f"Dog.gif")
        await interaction.followup.send(content=f"Dog:\n`/dog expression:{expression} clothes:{clothes} hat:{hat} hair:{hair} hat2:{hat2} animation:{animation} animated:{animated} body_col:{('#%02x%02x%02x' % body_col) if isinstance(body_col, tuple) else body_col} clothes_col:{('#%02x%02x%02x' % clothes_col) if isinstance(clothes_col, tuple) else clothes_col} hat_col:{('#%02x%02x%02x' % hat_col) if isinstance(hat_col, tuple) else hat_col}`{extra_text}", file=file, view=view)
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
        view = discord.utils.MISSING
        if use_palette in ["Random", "None"]:
            value = (0b10000 * random_animation) + (0b01000 * animated) + (0b00100 * add_hat2) + (0b00010 * (use_palette == "Random")) + (0b00001 * use_in_game_colors)
            view = RandomRepeatView(value)
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
            extra_text=f"\nPalette: {chosen}" + (" - 1/1001 CHANCE!! GAY MODE IS ACTIVE!!" if active else ""), # shhh keep it secret please
            view=view
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