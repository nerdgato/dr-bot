import os
from discord import File
from easy_pil import Editor, load_image_async, Font
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Función bienvenida cargada correctamente.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel

        # Usar ruta relativa
        image_path = os.path.join(os.getcwd(), "images", "pic2.png")
        background = Editor(image_path)
        
        profile_pic = await load_image_async(str(member.avatar.url))
        profile = Editor(profile_pic).resize((150, 150)).circle_image()
        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=20, variant="light")

        background.paste(profile, (325, 90))
        background.ellipse((325, 90), 150, 150, outline="white", stroke_width=5)
        background.text((400, 260), f"¡BIENVENIDO A {member.guild.name.upper()}!", font=poppins, color="white", align="center")
        background.text((400, 325), f"{member.name}#{member.discriminator}", font=poppins_small, color="white", align="center")

        file = File(fp=background.image_bytes, filename="pic2.png")
        rules_channel = member.guild.get_channel(1114642946382364766)

        await channel.send(f"¡Bom dia {member.mention}! Para más informacion revisa {rules_channel.mention}.")
        await channel.send(file=file)

async def setup(client):
    await client.add_cog(Welcome(client))
