const sqlite3 = require('sqlite3').verbose();
const { Client, GatewayIntentBits, ButtonBuilder, ActionRowBuilder, ButtonStyle, Events, PermissionFlagsBits, ChannelType } = require('discord.js');
const path = require('path');
require('dotenv').config();

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,         
        GatewayIntentBits.GuildMessages,  
        GatewayIntentBits.MessageContent  
    ]
});

const sancionImageFile = path.join(__dirname, '..', 'images', 'sancion_eralawea.png');
const muteImageFile = path.join(__dirname, '..', 'images', 'muted.png');

function conectarDB() {
    return new sqlite3.Database('bouken.db', (err) => {
        if (err) {
            console.error('Error al conectar a la base de datos:', err.message);
        }
    });
}

function cargarSanciones(userId, callback) {
    const db = conectarDB();
    const query = 'SELECT id, motivo, fecha, imagen, estado, staff FROM sanciones WHERE user_id = ?';

    db.all(query, [userId], (err, rows) => {
        if (err) {
            console.error('Error al cargar sanciones:', err.message);
            callback(err, null);
        } else {
            callback(null, rows);
        }
        db.close((err) => {
            if (err) {
                console.error('Error al cerrar la base de datos:', err.message);
            }
        });
    });
}

client.once('ready', async () => {
    console.log('¡Bot listo!');
    
    await manejarCanalSanciones('1308814397321384081', sancionImageFile, 
        '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO.\n\n## LUEGO DE 3 SANCIONES ACTIVAS SERÁS BANEADO.\n## RECUERDA QUE DEBES RESPETAR LAS REGLAS DEL SERVIDOR.\n## TIENES 24 HORAS PARA APELAR CADA SANCIÓN.');
    
    await manejarCanalMuteos('1308131311034040340', muteImageFile,
        '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE MUTEADO, ESPERA A QUE TERMINE EL TIMER PARA PODER CHARLAR NUEVAMENTE.\n## REVISA TU MENCIÓN EN  ⁠<#1210343520582508634>.');
});

async function manejarCanalSanciones(canalId, imageFile, messageContent) {
    const canal = await client.channels.fetch(canalId);

    if (!canal) {
        console.log(`Canal ${canalId} no encontrado`);
        return;
    }

    const mensajes = await canal.messages.fetch({ limit: 1 });

    if (mensajes.size === 0) {
        await canal.send({
            files: [imageFile],
            content: messageContent,
            components: [
                new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('ver_sanciones_button')
                        .setLabel('Ver Sanciones')
                        .setStyle(ButtonStyle.Danger)
                )
            ]
        });
    }
}

async function manejarCanalMuteos(canalId, imageFile, messageContent) {
    const canal = await client.channels.fetch(canalId);

    if (!canal) {
        console.log(`Canal ${canalId} no encontrado`);
        return;
    }

    const mensajes = await canal.messages.fetch({ limit: 1 });

    if (mensajes.size === 0) {
        const mensaje = await canal.send({
            files: [imageFile],
            content: messageContent,
        });

        await mensaje.react('😭');
    }
}

client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isButton()) return;

    if (interaction.customId === 'ver_sanciones_button') {
        const userId = interaction.user.id;

        cargarSanciones(userId, async (err, sanciones) => {
            if (err) {
                await interaction.reply({ content: 'Hubo un error al cargar las sanciones.', ephemeral: true });
                return;
            }

            if (!sanciones || sanciones.length === 0) {
                await interaction.reply({ content: 'No tienes sanciones registradas.', ephemeral: true });
            } else {
                // Crear los embeds y agregar los botones
                const embeds = sanciones.map((sancion, index) => ({
                    title: `Sanción #${index + 1}`,
                    description: `**id_sanción:** ${sancion.id}\n**motivo:** ${sancion.motivo}\n**fecha:** ${sancion.fecha}\n**estado:** ${sancion.estado}\n**staff:** <@${sancion.staff}>`,
                    color: 0xFF0000,
                    image: { url: sancion.imagen },
                }));

                const actionRow = new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('apelar_sancion_button')
                        .setLabel('Quiero Apelar')
                        .setEmoji('⚖️')
                        .setStyle(ButtonStyle.Secondary)
                );

                await interaction.reply({
                    embeds: embeds,
                    components: [actionRow], 
                    ephemeral: true
                });
            }
        });
    }
});

client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isButton()) return;

    if (interaction.customId === 'apelar_sancion_button') {
        const guild = interaction.guild;
        const member = interaction.member;

        // Cargar sanciones del usuario
        cargarSanciones(member.id, async (err, sanciones) => {
            if (err) {
                console.error('Error al cargar sanciones:', err);
                await interaction.reply({
                    content: 'Ocurrió un error al verificar tus sanciones. Por favor, intenta nuevamente.',
                    ephemeral: true
                });
                return;
            }

            // Verificar si tiene sanciones activas
            const sancionesActivas = sanciones.filter(sancion => sancion.estado === 'activa');

            if (sancionesActivas.length === 0) {
                // Si no tiene sanciones activas, notificarlo
                await interaction.reply({
                    content: 'No tienes sanciones activas en este momento.',
                    ephemeral: true
                });
                return;
            }

            // Si tiene sanciones activas, proceder con la creación del canal
            const categoryId = '1332000870681804830';

            // Crear nombre del canal: {nickname}'s ticket
            const canalNombre = `${member.nickname || member.user.username}-ticket`.replace(/\s+/g, '-').toLowerCase();

            // Verificar si ya existe un canal con ese nombre (opcional para evitar spam)
            const canalExistente = guild.channels.cache.find(c =>
                c.name === canalNombre && c.parentId === categoryId
            );
            if (canalExistente) {
                await interaction.reply({
                    content: `Ya tienes un canal de apelación abierto: <#${canalExistente.id}>`,
                    ephemeral: true
                });
                return;
            }

            try {
                // Crear el canal
                const canal = await guild.channels.create({
                    name: canalNombre,
                    type: ChannelType.GuildText,
                    parent: categoryId,
                    permissionOverwrites: [
                        {
                            id: guild.roles.everyone, // bloquear a todos
                            deny: [PermissionFlagsBits.ViewChannel],
                        },
                        {
                            id: member.id, // permitir solo al usuario
                            allow: [
                                PermissionFlagsBits.ViewChannel,
                                PermissionFlagsBits.SendMessages,
                                PermissionFlagsBits.ReadMessageHistory
                            ],
                        },
                        {
                            id: client.user.id, // permitir al bot
                            allow: [
                                PermissionFlagsBits.ViewChannel,
                                PermissionFlagsBits.SendMessages,
                                PermissionFlagsBits.ReadMessageHistory,
                                PermissionFlagsBits.ManageChannels
                            ],
                        },
                    ]
                });

                // Calcular el timestamp actual + 1 minuto (60 segundos)
                const timestamp = Math.floor(Date.now() / 1000) + (20 * 60); // 20 minutos
                // Enviar mensaje dentro del canal nuevo
                await canal.send({
                    content: `Hola ${member}, para apelar una sanción, por favor usa el comando \`/apelar_sancion\` en este canal.\n\n` +
                            `⏳ El canal se cerrará <t:${timestamp}:R>. Tienes ese tiempo para enviar la apelación.`
                });
                
                setTimeout(async () => {
                    try {
                        await canal.delete('Canal de apelación cerrado automáticamente tras 1 minuto sin actividad.');
                    } catch (err) {
                        console.error(`No se pudo eliminar el canal ${canal.name}:`, err);
                    }
                }, 20 * 60 * 1000); // Para 20 minutos
                

                // Confirmar en el canal original que se creó el canal
                await interaction.reply({
                    content: `Se ha creado un canal privado para tu apelación: <#${canal.id}>`,
                    ephemeral: true
                });
            } catch (error) {
                console.error('Error al crear canal de apelación:', error);
                await interaction.reply({
                    content: 'Ocurrió un error al crear el canal de apelación. Por favor, intenta nuevamente.',
                    ephemeral: true
                });
            }
        });
    }
});


client.on('messageCreate', async (message) => {
    // Asegurarse de que es el canal específico, el mensaje viene del bot y contiene embeds
    if (
        message.channelId === '1358223294112989474' &&
        message.author.id === client.user.id &&
        message.embeds.length > 0
    ) {
        try {
            const botones = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId('aprobar_button')
                    .setLabel('Aprobar')
                    .setStyle(ButtonStyle.Success),
                new ButtonBuilder()
                    .setCustomId('rechazar_button')
                    .setLabel('Rechazar')
                    .setStyle(ButtonStyle.Danger)
            );

            await message.edit({
                components: [botones]
            });

            console.log(`Botones agregados al mensaje con ID ${message.id}`);
        } catch (error) {
            console.error('Error al editar el mensaje con botones:', error);
        }
    }
});


client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isButton()) return;

    if (interaction.customId === 'aprobar_button' || interaction.customId === 'rechazar_button') {
        const aprobado = interaction.customId === 'aprobar_button';

        const botonFinal = new ActionRowBuilder().addComponents(
            new ButtonBuilder()
                .setCustomId('final_button')
                .setLabel(aprobado ? 'Aprobada' : 'Rechazada')
                .setStyle(aprobado ? ButtonStyle.Success : ButtonStyle.Danger)
                .setDisabled(true)
        );

        try {
            // Editar el mensaje original para reemplazar los botones
            await interaction.update({
                components: [botonFinal]
            });
        } catch (err) {
            console.error('Error al actualizar el mensaje con el botón final:', err);
        }
    }
});



client.login(process.env.DISCORD_TOKEN);
