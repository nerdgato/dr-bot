import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import json
import requests
import os
from cogs.database import inicializar_db, guardar_sancion, cargar_sanciones, actualizar_sancion_con_imagen, conectar_db, guardar_apelacion, cargar_apelaciones_por_usuario, cargar_apelaciones_por_sancion, actualizar_apelacion_imagen, actualizar_estado_apelacion
from dotenv import load_dotenv
import asyncio
import time

load_dotenv()


inicializar_db()


def subir_a_imgur_directo(imagen_data, sancion_id):
    client_id = os.getenv("IMGUR_CLIENT_ID")  
    
    headers = {'Authorization': f'Client-ID {client_id}'}
    data = {
        'type': 'file',
        'title': f'Sanción de Discord #{sancion_id}',
        'description': 'Imagen subida automáticamente desde el bot de Discord.'
    }
    url = "https://api.imgur.com/3/image"
    files = {'image': imagen_data}

    response = requests.post(url, headers=headers, data=data, files=files)
    if response.status_code == 200:
        response_data = response.json()
        return response_data['data']['link']
    else:
        print(f"Error al subir la imagen: {response.text}")
        return None


class slash_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        with open(os.path.join("data/media.json"), "r") as f:
            media_data = json.load(f)
            self.gifs = media_data.get("gifs", {})

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f"Comandos slash sincronizados en {len(self.client.guilds)} servidores.")

    @app_commands.command(name="sancionar", description="Sanciona a un jugador con un tipo de sanción específico")
    async def sancionar(self, interaction: discord.Interaction, member: discord.Member, tipo_sancion: str, evidencia: discord.Attachment):
        await interaction.response.defer(thinking=True, ephemeral=True)  # <--- línea nueva

        tipos_permitidos = ["spam", "toxicidad", "flood", "off-topic"]
        if tipo_sancion.lower() not in tipos_permitidos:
            await interaction.followup.send(
                "Tipo de sanción no válido. Los tipos permitidos son: spam, toxicidad, flood, off-topic."
            )
            return

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.followup.send(
                "No tienes permisos para sancionar a otros usuarios."
            )
            return

        if evidencia is None:
            await interaction.followup.send(
                "Es obligatorio proporcionar una imagen para la sanción."
            )
            return

        fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M")
        estado = 'activa'  
        staff_id = str(interaction.user.id)  
        sancion_id = guardar_sancion(str(member.id), tipo_sancion, fecha_actual, None, estado, staff_id)

        imagen_data = await evidencia.read()
        url_imagen = subir_a_imgur_directo(imagen_data, sancion_id)

        actualizar_sancion_con_imagen(sancion_id, url_imagen)

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios
                SET cant_sanciones = cant_sanciones + 1
                WHERE discord_id = ?
            ''', (str(member.id),))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al actualizar las sanciones del usuario {member.name}: {e}")
            await interaction.followup.send("Error al actualizar la base de datos.")
            return

        rol_sancion = discord.utils.get(interaction.guild.roles, name="Sanctioned")
        if not rol_sancion:
            await interaction.followup.send("El rol 'Sanctioned' no existe en el servidor.")
            return

        await member.add_roles(rol_sancion)

        await interaction.followup.send(
            f"{member.mention} ha sido sancionado por {tipo_sancion}. Imagen: {url_imagen}"
        )

        
    @sancionar.autocomplete("tipo_sancion")
    async def sancionar_tipo_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        tipos_permitidos = ["spam", "toxicidad", "flood", "off-topic"]

        # Filtrar según lo que el usuario está escribiendo actualmente
        opciones_filtradas = [
            tipo for tipo in tipos_permitidos if current.lower() in tipo.lower()
        ]

        # Retornar como lista de Choices
        return [
            app_commands.Choice(name=tipo, value=tipo) for tipo in opciones_filtradas
        ]


    
    @app_commands.command(name="apelar_sancion", description="Apela una sanción existente")
    async def apelar_sancion(
        self,
        interaction: discord.Interaction,
        id_sancion: int,
        razones: str,
        evidencia: discord.Attachment
    ):
        try:
            channel = interaction.channel

            # Validar si el canal está en la categoría correcta y sigue el formato del ticket
            if not channel or channel.category_id != 1332000870681804830 or not channel.name.endswith("-ticket"):
                await interaction.response.send_message(
                    "❌ Este comando solo puede usarse en canales de ticket. Consulta <#1308814397321384081>",
                    ephemeral=True
                )
                return

            user_id = str(interaction.user.id)

            # Verificar que la sanción ingresada pertenece al usuario y está activa
            sanciones = cargar_sanciones(user_id)
            sancion_valida = next((s for s in sanciones if s[0] == id_sancion and s[4].lower() == 'activa'), None)

            if not sancion_valida:
                await interaction.response.send_message(
                    f"❌ Error al apelar: La sanción con ID **{id_sancion}** no existe, no está activa o no está asociada a tu usuario.",
                    ephemeral=True
                )
                return

            if not razones:
                await interaction.response.send_message(
                    "Debes proporcionar una razón para apelar la sanción.", ephemeral=True
                )
                return

            if evidencia is None:
                await interaction.response.send_message(
                    "Es obligatorio proporcionar una imagen para la apelación.", ephemeral=True
                )
                return

            # Leer la imagen y subirla a Imgur
            imagen_data = await evidencia.read()
            url_imgur = subir_a_imgur_directo(imagen_data, id_sancion)

            if url_imgur is None:
                await interaction.response.send_message(
                    "❌ Ocurrió un error al subir la imagen a Imgur. Intenta nuevamente más tarde.", ephemeral=True
                )
                return

            # Guardar la apelación en la base de datos
            apelacion_id = guardar_apelacion(
                sancion_id=id_sancion,
                user_id=user_id,
                razones=razones,
                evidencia=url_imgur
            )

            # Crear el embed para notificar en el canal de logs
            log_channel_id = 1358223294112989474
            log_channel = interaction.client.get_channel(log_channel_id)

            # Confirmación al usuario y cierre del ticket
            timestamp = int(time.time()) + 11
            await interaction.response.send_message(
                f"✅ Tu apelación ha sido registrada correctamente.\n"
                f"🖼️ Evidencia subida: {url_imgur}\n\n"
                f"⏳ Este canal se cerrará automáticamente <t:{timestamp}:R>.\n\n",
                ephemeral=True
            )
            
            if log_channel:
                embed = discord.Embed(
                    title="📢 Nueva Apelación Recibida",
                    color=discord.Color.yellow()
                )
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
                embed.add_field(name="🆔 Sanción", value=str(id_sancion), inline=False)
                embed.add_field(name="📝 Razón de Apelación", value=razones, inline=False)
                embed.set_image(url=url_imgur)

                await log_channel.send(embed=embed)

            await asyncio.sleep(9)
            await channel.delete(reason="Cierre automático tras apelación.")

        except Exception as e:
            print(f"Error al apelar sanción: {e}")
            await interaction.response.send_message(
                "❌ Ocurrió un error al intentar apelar la sanción.", ephemeral=True
            )


    
    @apelar_sancion.autocomplete("id_sancion")
    async def apelar_sancion_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        # Obtener el ID del usuario que ejecuta el comando
        user_id = str(interaction.user.id)

        # Cargar las sanciones activas del usuario
        sanciones = cargar_sanciones(user_id)

        # Filtrar las sanciones activas
        sanciones_activas = [
            sancion for sancion in sanciones if sancion[4].lower() == 'activa'
        ]

        # Si no hay sanciones activas, no completar el campo
        if not sanciones_activas:
            return []

        # Filtrar las sanciones que coincidan con la búsqueda del usuario
        opciones = [
            sancion for sancion in sanciones_activas if current.lower() in str(sancion[0]).lower()
        ]

        # Retornar las opciones para autocompletar
        return [
            app_commands.Choice(name=str(sancion[0]), value=str(sancion[0])) for sancion in opciones
        ]
       
    

    @app_commands.command(name="ver_sanciones", description="Muestra las sanciones de un jugador")
    async def ver_sanciones(self, interaction: discord.Interaction, member: discord.Member):
        try:
            
            await interaction.response.defer(ephemeral=True)

            
            sanciones = cargar_sanciones(str(member.id))

            
            if not sanciones:
                await interaction.followup.send(
                    f"{member.mention} no tiene sanciones registradas.", ephemeral=True
                )
                return

            
            for sancion in sanciones:
                sancion_id, motivo, fecha, imagen, estado, staff_id = sancion

                
                staff_member = await interaction.guild.fetch_member(staff_id)
                staff_mention = staff_member.mention if staff_member else "Desconocido"

                
                embed = discord.Embed(
                    title=f"Sanción ID: {sancion_id}",
                    description=f"Detalles de la sanción para {member.mention}",
                    color=0xFF0000,
                )
                embed.add_field(name="Motivo", value=motivo, inline=False)
                embed.add_field(name="Fecha", value=fecha, inline=False)
                embed.add_field(name="Estado", value=estado, inline=False)
                embed.add_field(name="Staff", value=staff_mention, inline=False)

                
                if imagen:
                    embed.set_image(url=imagen)

                
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error al cargar sanciones: {e}")
            await interaction.followup.send(
                "Ocurrió un error al intentar cargar las sanciones.", ephemeral=True
            )

    @app_commands.command(name="remover_sancion", description="Revoca una sanción de un jugador.")
    async def remover_sancion(self, interaction: discord.Interaction, member: discord.Member, id_sancion: int):

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "No tienes permisos para remover sanciones.", ephemeral=True
            )
            return

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Buscar sanciones activas
            cursor.execute('''
                SELECT id, motivo, fecha, imagen, estado
                FROM sanciones
                WHERE user_id = ? AND estado = 'activa'
            ''', (str(member.id),))
            sanciones = cursor.fetchall()

            if not sanciones:
                await interaction.response.send_message(
                    f"{member.mention} no tiene sanciones activas registradas.", ephemeral=True
                )
                conn.close()
                return

            if id_sancion not in [s[0] for s in sanciones]:
                await interaction.response.send_message(
                    f"El ID {id_sancion} no corresponde a una sanción activa válida.", ephemeral=True
                )
                conn.close()
                return

            # Marcar la sanción como revocada
            cursor.execute('''
                UPDATE sanciones
                SET estado = 'revocada'
                WHERE id = ?
            ''', (id_sancion,))
            conn.commit()

            # Restar 1 al contador de sanciones activas del usuario
            cursor.execute('''
                UPDATE usuarios
                SET cant_sanciones = cant_sanciones - 1
                WHERE discord_id = ?
            ''', (str(member.id),))
            conn.commit()

            # Obtener la apelación relacionada con la sanción
            cursor.execute('''
                SELECT id
                FROM apelaciones
                WHERE sancion_id = ? AND estado = 'pendiente'
            ''', (id_sancion,))
            apelacion = cursor.fetchone()

            if apelacion:
                # Actualizar estado de la apelación a "aprobada"
                actualizar_estado_apelacion(apelacion[0], 'aprobada')

            conn.close()

            await interaction.response.send_message(
                f"La sanción con ID {id_sancion} fue revocada correctamente. Se actualizó el contador de sanciones activas de {member.mention}.",
                ephemeral=True
            )

        except Exception as e:
            print(f"Error al revocar la sanción: {e}")
            await interaction.response.send_message(
                "Ocurrió un error al intentar revocar la sanción.", ephemeral=True
            )



    @remover_sancion.autocomplete("id_sancion")
    async def remover_sancion_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[int]]:
        
        # Intentar obtener el miembro (puede que no esté aún definido en el autocompletado)
        member = interaction.namespace.member or interaction.user

        if not member:
            return []

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, estado
                FROM sanciones
                WHERE user_id = ?
            ''', (str(member.id),))
            sanciones = cursor.fetchall()
            conn.close()

            # Filtrar solo las sanciones activas
            sanciones_activas = [s for s in sanciones if s[1].lower() == 'activa']

            # Filtrar por búsqueda parcial del usuario
            if current.isdigit():
                sanciones_filtradas = [
                    s[0] for s in sanciones_activas if current in str(s[0])
                ]
            else:
                sanciones_filtradas = [s[0] for s in sanciones_activas]

            # Retornar las opciones como Choices de tipo int
            return [
                app_commands.Choice(name=f"{sancion_id}", value=int(sancion_id))
                for sancion_id in sanciones_filtradas[:25]  # Máximo 25 opciones
            ]

        except Exception as e:
            print(f"Error en autocomplete de remover_sancion: {e}")
            return []

        
   

    @app_commands.command(name="clear", description="Borra un número específico de mensajes en el canal actual")
    async def clear(self, interaction: discord.Interaction, cantidad: int):
        if cantidad <= 0:
            await interaction.response.send_message(
                "Por favor, proporciona un número entero positivo de mensajes a borrar.", ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "No tienes permisos para borrar mensajes en este canal.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        mensajes_borrados = 0
        async for mensaje in interaction.channel.history(limit=cantidad):
            await mensaje.delete()
            mensajes_borrados += 1
            await asyncio.sleep(2)

        await interaction.followup.send(
            f"Se han borrado {mensajes_borrados} mensajes.", ephemeral=True
        )
    
    @app_commands.command(name="mute", description="Mutea a un usuario por un tiempo determinado")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time_minutes: int):
        
        if time_minutes < 2:
            await interaction.response.send_message("El tiempo de muteo debe ser de al menos 2 minutos.", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("No tienes permisos para mutear a otros usuarios.", ephemeral=True)
            return
        
        
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        timestamp = interaction.created_at.timestamp()
        
        
        if not mute_role:
            try:
                mute_role = await interaction.guild.get_role(1210341291821371403)
                for channel in interaction.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False)
            except discord.Forbidden:
                await interaction.response.send_message("No tengo permisos para obtener el rol de mute.", ephemeral=True)
                return
        
        
        await member.add_roles(mute_role)
        await interaction.response.send_message(f"El usuario {member.mention} ha sido muteado por {time_minutes} minutos.", ephemeral=True)
        
        
        log_channel = interaction.guild.get_channel(1210343520582508634)  
        if log_channel:
            initial_message = await log_channel.send(f"El usuario {member.mention} ha sido muteado por {interaction.user.mention}. Volverá <t:{int(timestamp + (time_minutes*60))}:R>")
            gif_url = self.gifs.get("muted")
            await log_channel.send(gif_url)
        
        await asyncio.sleep(time_minutes * 60)
        
        
        await member.remove_roles(mute_role)
        await initial_message.edit(content=f"{member.mention} fue muteado por {interaction.user.mention}. *Volvió a los {time_minutes} minutos*  :white_check_mark:")
    
    @app_commands.command(name="registrar_usuario", description="Registra a un usuario específico en la base de datos")
    @app_commands.describe(usuario="Selecciona al usuario que deseas registrar")
    async def registrar_usuario(self, interaction: discord.Interaction, usuario: discord.Member):
        await interaction.response.defer(ephemeral=True)

        bot_roles_ids = {1213624079131746434, 1114642945094725767}
        roles_excluidos = {1308823767820013658, 1210341291821371403}

        tiene_rol_bot = any(role.id in bot_roles_ids for role in usuario.roles)

        if tiene_rol_bot:
            await interaction.followup.send(f"❌ No se puede registrar a un bot o sistema.")
            return

        # Filtrar roles válidos
        roles_validos = [
            role for role in usuario.roles
            if role.id not in roles_excluidos and role.name != "@everyone"
        ]

        rol_mayor_prioridad = max(roles_validos, key=lambda r: r.position).name if roles_validos else "Sin rol"

        try:
            conn = conectar_db()
            cursor = conn.cursor()

            # Intentar insertar
            cursor.execute('''
                INSERT INTO usuarios (discord_id, nombre_usuario, rol_actual)
                VALUES (?, ?, ?)
            ''', (str(usuario.id), usuario.name, rol_mayor_prioridad))

            if cursor.rowcount == 0:
                await interaction.followup.send(f"⚠️ El usuario {usuario.mention} ya estaba registrado.")
            else:
                await interaction.followup.send(f"✅ Usuario {usuario.mention} registrado correctamente.")

            conn.commit()
            conn.close()

        except Exception as e:
            await interaction.followup.send(f"❌ Error al registrar a {usuario.mention}: {e}")
       
async def setup(client: commands.Bot):
    await client.add_cog(slash_commands(client))
