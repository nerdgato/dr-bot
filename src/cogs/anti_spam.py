import discord
from discord.ext import commands
from collections import defaultdict
import asyncio
import json
import os

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}
        self.mute_time = 300  # Tiempo de mute en segundos
        with open(os.path.join("data", "media.json"), "r") as f:
            media_data = json.load(f)
            self.gifs = media_data.get("gifs", {})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        timestamp = message.created_at.timestamp()

        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []

        # Verificar si el usuario tiene el rol que indica silencio
        if any(role.id == 1210341291821371403 for role in message.author.roles):
            return  # Salir del método sin procesar más

        # Verificar si el usuario ha enviado mensajes recientemente
        if len(self.spam_tracker[user_id]) >= 5:
            oldest_msg = self.spam_tracker[user_id][0]
            if timestamp - oldest_msg < 5:  # Si envió más de 5 mensajes en menos de 5 segundos
                # Silenciar al usuario
                mute_role = message.guild.get_role(1210341291821371403)
                await message.author.add_roles(mute_role)
                channel = message.guild.get_channel(1210343520582508634)
                # Enviar el mensaje inicial con la cuenta regresiva
                initial_message = await channel.send(f"{message.author.mention} ha sido silenciado por spam. Volverá <t:{int(timestamp + self.mute_time)}:R>")
                # Obtener la URL del gif desde el archivo JSON
                gif_url = self.gifs.get("muted")
                await channel.send(gif_url)

                # Borrar todos los mensajes recientes del usuario excepto el primero
                messages_to_delete = self.spam_tracker[user_id][1:]
                for msg_timestamp in messages_to_delete:
                    async for msg in message.channel.history(limit=100):
                        if msg.author.id == user_id and msg.created_at.timestamp() == msg_timestamp:
                            await msg.delete()

                # Iniciar temporizador para levantar el silencio después del tiempo especificado
                await asyncio.sleep(self.mute_time)
                # Modificar el mensaje para eliminar el timestamp
                await initial_message.edit(content=f"{message.author.mention} fue silenciado por spam. {int(self.mute_time // 60)}  :white_check_mark:")   
                # Levantar el silencio
                await message.author.remove_roles(mute_role)
                # Limpiar la lista de mensajes del usuario
                self.spam_tracker[user_id] = []

        # Agregar el mensaje actual a la lista de mensajes del usuario
        self.spam_tracker[user_id].append(timestamp)

        # Mantener solo los últimos 5 mensajes del usuario en el registro
        if len(self.spam_tracker[user_id]) > 5:
            self.spam_tracker[user_id] = self.spam_tracker[user_id][-5:]

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))