const sqlite3 = require('sqlite3').verbose();
const { Client, GatewayIntentBits, ButtonBuilder, ActionRowBuilder, ButtonStyle, Events } = require('discord.js');
const path = require('path');
require('dotenv').config();

// Crear cliente de Discord
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,         // Para interactuar con servidores
        GatewayIntentBits.GuildMessages,  // Para leer mensajes
        GatewayIntentBits.MessageContent  // Para obtener el contenido del mensaje
    ]
});

// Rutas de imágenes
const sancionImageFile = path.join(__dirname, '..', 'images', 'sancion_eralawea.png');
const muteImageFile = path.join(__dirname, '..', 'images', 'muted.png');

// Función para conectar a la base de datos
function conectarDB() {
    return new sqlite3.Database('bouken.db', (err) => {
        if (err) {
            console.error('Error al conectar a la base de datos:', err.message);
        } else {
            console.log('Conectado a la base de datos SQLite.');
        }
    });
}

// Función para cargar sanciones de un usuario
function cargarSanciones(userId, callback) {
    const db = conectarDB();
    const query = 'SELECT id, motivo, fecha, imagen FROM sanciones WHERE user_id = ?';

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
            } else {
                console.log('Base de datos cerrada.');
            }
        });
    });
}

// Evento cuando el bot se conecta y está listo
client.once('ready', async () => {
    console.log('¡Bot listo!');
    
    // Canal de sanciones
    await manejarCanalSanciones('1308814397321384081', sancionImageFile, 
        '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO. LUEGO DE 3 SANCIONES SERÁS BANEADO.\n## RECUERDA QUE DEBES RESPETAR LAS REGLAS DEL SERVIDOR.\n## TIENES 24 HORAS PARA APELAR CADA SANCIÓN.');

    // Canal de muteos
    await manejarCanalMuteos('1308131311034040340', muteImageFile,
        '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE MUTEADO, ESPERA A QUE TERMINE EL TIMER PARA PODER CHARLAR NUEVAMENTE.\n## REVISA TU MENCIÓN EN  ⁠<#1210343520582508634>.');
});




// Manejar el canal de sanciones
async function manejarCanalSanciones(canalId, imageFile, messageContent) {
    const canal = await client.channels.fetch(canalId);

    if (!canal) {
        console.log(`Canal ${canalId} no encontrado`);
        return;
    }

    // Buscar el primer mensaje en el canal
    const mensajes = await canal.messages.fetch({ limit: 1 });

    if (mensajes.size === 0) {
        // Si no existe el primer mensaje, crear el mensaje inicial con la imagen, texto y botón
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

// Manejar el canal de muteos
async function manejarCanalMuteos(canalId, imageFile, messageContent) {
    const canal = await client.channels.fetch(canalId);

    if (!canal) {
        console.log(`Canal ${canalId} no encontrado`);
        return;
    }

    // Buscar el primer mensaje en el canal
    const mensajes = await canal.messages.fetch({ limit: 1 });

    if (mensajes.size === 0) {
        // Si no existe el primer mensaje, crear el mensaje inicial con la imagen, texto y reacción
        const mensaje = await canal.send({
            files: [imageFile],
            content: messageContent,
        });

        // Agregar la reacción
        await mensaje.react('😭');
    }
}

// Manejar la interacción con el botón
client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isButton()) return;

    if (interaction.customId === 'ver_sanciones_button') {
        const userId = interaction.user.id;
        
        // Pasar el userId y manejar el callback
        cargarSanciones(userId, async (err, sanciones) => {
            if (err) {
                await interaction.reply({ content: 'Hubo un error al cargar las sanciones.', ephemeral: true });
                return;
            }

            if (!sanciones || sanciones.length === 0) {
                await interaction.reply({ content: 'No tienes sanciones registradas.', ephemeral: true });
            } else {
                const embeds = sanciones.map((sancion, index) => {
                    return {
                        title: `Sanción ${index + 1}`,
                        description: `**Motivo:** ${sancion.motivo}\n**Fecha:** ${sancion.fecha}`,
                        color: 0xFF0000,
                        image: { url: sancion.imagen } // Si quieres incluir la imagen
                    };
                });

                await interaction.reply({ embeds: embeds, ephemeral: true });
            }
        });
    }
});

// Login del bot con el token desde .env
client.login(process.env.DISCORD_TOKEN);