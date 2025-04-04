import os
from discord import File
from easy_pil import Editor, load_image_async, Font
from discord.ext import commands
from cogs.database import conectar_db  

class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Función bienvenida cargada correctamente.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel

        # Registrar usuario en la base de datos
        await self.registrar_usuario(member)

        # Crear imagen de bienvenida
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

        await channel.send(f"¡Bom dia {member.mention}! Para más información revisa {rules_channel.mention}.")
        await channel.send(file=file)

    async def registrar_usuario(self, member):
        """ Registra un nuevo usuario en la base de datos SQLite. """
        try:
            conn = conectar_db()
            cursor = conn.cursor()

            # Determinar el rol de mayor prioridad (si tiene roles asignados)
            roles_excluidos = {1308823767820013658, 1210341291821371403}  
            roles_validos = [role for role in member.roles if role.id not in roles_excluidos and role.name != "@everyone"]
            rol_mayor_prioridad = max(roles_validos, key=lambda r: r.position).name if roles_validos else "Sin rol"

            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (discord_id, nombre_usuario, rol_actual)
                VALUES (?, ?, ?)
            ''', (str(member.id), member.name, rol_mayor_prioridad))

            conn.commit()
            conn.close()
            print(f"Usuario {member.name} registrado correctamente en la base de datos.")

        except Exception as e:
            print(f"Error al registrar a {member.name}: {e}")

async def setup(client):
    await client.add_cog(Welcome(client))
