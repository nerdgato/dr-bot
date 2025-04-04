const sqlite3 = require('sqlite3').verbose();
const { Client, GatewayIntentBits, ButtonBuilder, ActionRowBuilder, ButtonStyle, Events } = require('discord.js');
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
    const query = 'SELECT id, motivo, fecha, imagen, staff FROM sanciones WHERE user_id = ?';

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
        '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO. LUEGO DE 3 SANCIONES SERÁS BANEADO.\n## RECUERDA QUE DEBES RESPETAR LAS REGLAS DEL SERVIDOR.\n## TIENES 24 HORAS PARA APELAR CADA SANCIÓN.');


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
                    description: `**id_sanción:** ${sancion.id}\n**motivo:** ${sancion.motivo}\n**fecha:** ${sancion.fecha}\n**staff:** <@${sancion.staff}>`,
                    color: 0xFF0000,
                    image: { url: sancion.imagen },
                }));


                const actionRow = new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('apelar_sancion_button')
                        .setLabel('Apelar')
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


client.login(process.env.DISCORD_TOKEN);
