import discord
from discord.ext import commands
from cogs.database import conectar_db

class Normas(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog de Normas cargado correctamente.")
        
        
        channel_id = 1114642946382364766
        message_id = 1308243954042667081

        channel = self.client.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        
        emoji = "<:docyes:1212972475755929670>"
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        
        if payload.channel_id == 1114642946382364766 and payload.message_id == 1308243954042667081:
            guild = self.client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(1114642945094725768)  

            
            if role not in member.roles and str(payload.emoji) == "<:docyes:1212972475755929670>":
                await member.add_roles(role)
                try:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE usuarios
                        SET rol_actual = ?
                        WHERE discord_id = ?
                    ''', (role.name, str(member.id)))

                    conn.commit()
                    conn.close()
                    print(f"Rol de {member.name} actualizado a '{role.name}' en la base de datos.")
                except Exception as e:
                    print(f"Error al actualizar el rol de {member.name}: {e}")

async def setup(client):
    await client.add_cog(Normas(client))
