import discord
from discord.ext import commands

class Normas(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog de Normas cargado correctamente.")
        
        # Obtener el canal de destino y el mensaje de las normas
        channel_id = 1114642946382364766  # ID del canal de destino
        message_id = 1212923083900321793  # ID del mensaje de las normas

        channel = self.client.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        # Añadir la reacción al mensaje
        emoji = "<:docyes:1212972475755929670>"
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Verificar que la reacción ocurrió en el mensaje de las normas
        if payload.channel_id == 1114642946382364766 and payload.message_id == 1212923083900321793:
            guild = self.client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(1114642945094725768)  # ID del rol a asignar

            # Verificar si el usuario no tiene el rol y la reacción es la esperada
            if role not in member.roles and str(payload.emoji) == "<:docyes:1212972475755929670>":
                await member.add_roles(role)

async def setup(client):
    await client.add_cog(Normas(client))
