// Importar la librería dotenv para cargar variables de entorno
require('dotenv').config();

// Importar la librería discord.js
const { Client, GatewayIntentBits, ButtonBuilder, ActionRowBuilder, ButtonStyle, Events } = require('discord.js');
const fs = require('fs');
const path = require('path');

// Crear cliente de Discord
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,         // Para interactuar con servidores
        GatewayIntentBits.GuildMessages,  // Para leer mensajes
        GatewayIntentBits.MessageContent  // Para obtener el contenido del mensaje
    ]
});

// Ruta del archivo de sanciones
const sancionesFile = path.join(__dirname, '..', 'data', 'sanciones.json');

// Rutas de imágenes
const sancionImageFile = path.join(__dirname, '..', 'images', 'sancion_eralawea.png');
const muteImageFile = path.join(__dirname, '..', 'images', 'muted.png');

// Cargar las sanciones desde el archivo JSON
function cargarSanciones() {
    if (fs.existsSync(sancionesFile)) {
        const rawData = fs.readFileSync(sancionesFile);
        return JSON.parse(rawData);
    }
    return {};
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
        const sanciones = cargarSanciones();

        if (!sanciones[userId] || sanciones[userId].length === 0) {
            await interaction.reply({ content: 'No tienes sanciones registradas.', ephemeral: true });
        } else {
            const embeds = sanciones[userId].map((sancion, index) => {
                return {
                    title: `Sanción ${index + 1}`,
                    description: `**Motivo:** ${sancion.motivo}\n**Fecha:** ${sancion.fecha}`,
                    color: 0xFF0000
                };
            });

            await interaction.reply({ embeds: embeds, ephemeral: true });
        }
    }
});

// Login del bot con el token desde .env
client.login(process.env.DISCORD_TOKEN);
