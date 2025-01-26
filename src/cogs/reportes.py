# import discord
# from discord.ext import commands

# class Reportes(commands.Cog):
#     def __init__(self, client):
#         self.client = client
#         self.procesados = {}
#         self.lupa_reaccionada = set()

#     @commands.Cog.listener()
#     async def on_ready(self):
#         print("Cog de Reportes cargado correctamente.")

#     @commands.Cog.listener()
#     async def on_message(self, message):
#         if message.channel.id == 1210224491913814088 and message.embeds:
#             report_titles = ["bug", "problema", "error"]
#             if message.embeds[0].title.lower() in report_titles:
#                 if message.id not in self.procesados:
#                     await message.add_reaction("🔍")
#                     self.lupa_reaccionada.add(message.id)

#     @commands.Cog.listener()
#     async def on_raw_reaction_add(self, payload):
#         if payload.channel_id == 1210224491913814088 and payload.user_id != self.client.user.id:
#             channel = self.client.get_channel(payload.channel_id)
#             message = await channel.fetch_message(payload.message_id)

#             if message.id in self.procesados:
#                 usuario_inicial = self.procesados[message.id]
#                 usuario_reaccion = await self.client.fetch_user(payload.user_id)
#                 if usuario_reaccion.id != usuario_inicial.id:
#                     return

#             report_id = message.embeds[0].footer.text.split("#")[1]
#             report_content = message.embeds[0].description
#             report_content_original = report_content

#             usuario_reaccion = await self.client.fetch_user(payload.user_id)

#             if str(payload.emoji) == "🔍" and message.id not in self.procesados:
#                 log_action = "Tomado"
#                 log_color = discord.Color.gold()
#                 await message.add_reaction("✅")
#                 self.procesados[message.id] = usuario_reaccion

#                 mentioned_user = self.extract_mentioned_user(report_content_original)
#                 if mentioned_user:
#                     thumbnail_url = "https://i.imgur.com/kwULhbl.png"
#                     embed = discord.Embed(
#                         title="Reporte Tomado",
#                         description=f"¡Tu reporte ha sido tomado! Estaremos en contacto contigo si necesitamos más información.",
#                         color=discord.Color.yellow()
#                     )
#                     embed.set_thumbnail(url=thumbnail_url)
#                     embed.set_footer(text=f"BOUKENCRAFT TEAM - ID del Reporte: {report_id}")

#                     try:
#                         await mentioned_user.send(embed=embed)
#                     except discord.Forbidden:
#                         print("El usuario ha desactivado los mensajes directos.")

#                     await self.send_report_log(message, usuario_reaccion, report_id, report_content_original, log_action, log_color)

#                 else:  # Si no hay usuario mencionado
#                     log_channel = self.client.get_channel(1212423583825924146)
#                     staff_member = await self.client.fetch_user(usuario_reaccion.id)
#                     log_embed = discord.Embed(
#                         title=f"Reporte #{report_id} {log_action}",
#                         description=f"{self.clean_report_content(report_content_original)}\n\nstaff {staff_member.mention}",
#                         color=log_color,
#                     )
#                     log_embed.set_thumbnail(url=staff_member.avatar.url)
#                     log_embed.set_footer(text=f"BOUKENCRAFT TEAM - ID del Reporte: {report_id}")

#                     await log_channel.send(embed=log_embed)

#             elif str(payload.emoji) == "✅":
#                 log_action = "Cerrado"
#                 log_color = discord.Color.green()
#                 await self.send_report_closed_message(message, usuario_reaccion, report_id, report_content_original, log_action, log_color)

#     async def send_report_log(self, message, usuario_reaccion, report_id, report_content_original, log_action, log_color):
#         thumbnail_url = usuario_reaccion.avatar.url
#         embed = discord.Embed(
#             title=f"Reporte #{report_id} {log_action}",
#             description=f"{self.clean_report_content(report_content_original)}\n\nstaff {usuario_reaccion.mention}",
#             color=log_color,
#         )
#         embed.set_thumbnail(url=thumbnail_url)
#         embed.set_footer(text=f"BOUKENCRAFT TEAM - ID del Reporte: {report_id}")

#         log_channel = self.client.get_channel(1212423583825924146)
#         await log_channel.send(embed=embed)

#     async def send_report_closed_message(self, message, usuario_reaccion, report_id, report_content_original, log_action, log_color):
#         mentioned_user = self.extract_mentioned_user(report_content_original)

#         if mentioned_user:
#             thumbnail_url = "https://i.imgur.com/krv57l5.png"
#             embed = discord.Embed(
#                 title="Reporte Cerrado",
#                 description="¡Tu reporte ha sido cerrado! Gracias por tu contribución.",
#                 color=discord.Color.green()
#             )
#             embed.set_thumbnail(url=thumbnail_url)
#             embed.set_footer(text=f"BOUKENCRAFT TEAM - ID del Reporte: {report_id}")

#             try:
#                 await mentioned_user.send(embed=embed)
#             except discord.Forbidden:
#                 print("El usuario ha desactivado los mensajes directos.")

#         await self.send_report_log(message, usuario_reaccion, report_id, report_content_original, log_action, log_color)

#     def extract_mentioned_user(self, content):
#         if "<@" in content:
#             user_id = content.split("<@")[-1].split(">")[0]
#             try:
#                 return self.client.get_user(int(user_id))
#             except ValueError:
#                 return None
#         return None

#     def clean_report_content(self, content):
#         return content.split("\n\nby ")[0]

# async def setup(client):
#     await client.add_cog(Reportes(client))
