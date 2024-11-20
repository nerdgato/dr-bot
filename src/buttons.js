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

// Ruta del archivo de sanciones (modificada para acceder a la carpeta data fuera de src)
const sancionesFile = path.join(__dirname, '..', 'data', 'sanciones.json');

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
    const canalId = '1308814397321384081';  // El ID del canal donde se debe agregar el botón
    const canal = await client.channels.fetch(canalId);  // Obtener el canal

    if (!canal) {
        console.log('Canal no encontrado');
        return;
    }

    // Buscar el primer mensaje en el canal
    const mensajes = await canal.messages.fetch({ limit: 1 });

    if (mensajes.size === 0) {
        // Si no existe el primer mensaje, crear el mensaje inicial con el botón
        const primerMensaje = await canal.send({
            content: '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO.',
            components: [
                new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('ver_sanciones_button')
                        .setLabel('Ver Sanciones')
                        .setStyle(ButtonStyle.Danger)
                )
            ]
        });
    } else {
        // Si ya existe el primer mensaje, solo agregar el botón si no está presente
        const primerMensaje = mensajes.first();

        // Verificar si el mensaje ya tiene el botón
        const botonExistente = primerMensaje.components.some(row => 
            row.components.some(button => button.customId === 'ver_sanciones_button')
        );

        if (botonExistente) {
            console.log('El botón ya existe');
            return;
        }

        // Crear el botón y añadirlo en el mismo mensaje
        const button = new ButtonBuilder()
            .setCustomId('ver_sanciones_button')
            .setLabel('Ver Sanciones')
            .setStyle(ButtonStyle.Danger);

        const row = new ActionRowBuilder().addComponents(button);

        // Enviar el botón debajo del primer mensaje sin texto adicional
        await primerMensaje.channel.send({
            content: '# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO.',
            components: [row],
        });
    }
});

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
