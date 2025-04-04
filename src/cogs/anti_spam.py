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
        self.banned_gif_keyword = "caption.gif"  
        with open(os.path.join("data", "media.json"), "r") as f:
            media_data = json.load(f)
            self.gifs = media_data.get("gifs", {})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return


        if self.banned_gif_keyword in message.content:
            await message.delete()
            return  

        user_id = message.author.id
        timestamp = message.created_at.timestamp()

        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []

        # Verificar si el usuario tiene el rol que indica silencio
        if any(role.id == 1210341291821371403 for role in message.author.roles):
            return  

        # Verificar si el usuario ha enviado mensajes recientemente
        if len(self.spam_tracker[user_id]) >= 5:
            oldest_msg = self.spam_tracker[user_id][0]
            if timestamp - oldest_msg < 5:  
                
                mute_role = message.guild.get_role(1210341291821371403)
                await message.author.add_roles(mute_role)
                channel = message.guild.get_channel(1210343520582508634)
                
                initial_message = await channel.send(f"{message.author.mention} ha sido silenciado por spam. Volverá <t:{int(timestamp + self.mute_time)}:R>")
                
                gif_url = self.gifs.get("muted")
                await channel.send(gif_url)

               
                messages_to_delete = self.spam_tracker[user_id][1:]
                for msg_timestamp in messages_to_delete:
                    async for msg in message.channel.history(limit=100):
                        if msg.author.id == user_id and msg.created_at.timestamp() == msg_timestamp:
                            await msg.delete()

                
                await asyncio.sleep(self.mute_time)
                
                await initial_message.edit(content=f"{message.author.mention} fue silenciado por spam. {int(self.mute_time // 60)}  :white_check_mark:")   
                
                await message.author.remove_roles(mute_role)
                
                self.spam_tracker[user_id] = []

        
        self.spam_tracker[user_id].append(timestamp)

        
        if len(self.spam_tracker[user_id]) > 5:
            self.spam_tracker[user_id] = self.spam_tracker[user_id][-5:]

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))