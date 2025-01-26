const {
    Client,
    GatewayIntentBits,
    ActionRowBuilder,
    ButtonBuilder,
    ButtonStyle,
    Events,
    EmbedBuilder,
    StringSelectMenuBuilder,
    ModalBuilder
} = require('discord.js');
require('dotenv').config();

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ],
});

const procesados = new Map();

client.once('ready', () => {
    console.log('¡Bot listo!');
});

client.on(Events.MessageCreate, async (message) => {
    if (message.channel.id === '1210224491913814088' && message.embeds.length > 0 && message.author.id === client.user.id) {
        const reportTitles = ["bug", "problema", "error"];
        const embed = message.embeds[0];

        if (reportTitles.includes(embed.title.toLowerCase()) && !procesados.has(message.id)) {
            const actionRow = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId(`take_report_${message.id}`)
                    .setLabel('Tomar Reporte')
                    .setStyle(ButtonStyle.Secondary),
                new ButtonBuilder()
                    .setCustomId(`reject_report_${message.id}`)
                    .setLabel('Rechazar Reporte')
                    .setStyle(ButtonStyle.Danger)
            );

            await message.edit({
                content: 'Haz clic en un botón para gestionar este reporte:',
                components: [actionRow]
            });
        }
    }
});


client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isButton() && !interaction.isStringSelectMenu()) return;

    const [action, , reportId] = interaction.customId.split('_');
    const staffMember = interaction.user;

    // Obtener el rango del staff (basado en el primer rol más alto que tenga)
    const staffRole = interaction.member.roles.highest;

    // Helper para extraer usuario mencionado
    const extractMentionedUser = (content) => {
        const mentionRegex = /<@!?(\d+)>/;
        const match = content.match(mentionRegex);
        if (match) {
            const userId = match[1];
            const user = client.users.cache.get(userId);
            if (!user) console.log(`Usuario no encontrado: ${userId}`);
            return user;
        } else {
            console.log('No se encontró una mención en el contenido:', content);
            return null;
        }
    };

    // Botón "Tomar Reporte"
    if (action === 'take') {
        if (procesados.has(reportId)) {
            await interaction.reply({ content: 'Este reporte ya ha sido tomado por otro miembro del staff.', ephemeral: true });
            return;
        }
    
        procesados.set(reportId, staffMember.id);
    
        try {
            const originalMessage = await interaction.channel.messages.fetch(reportId);
            const reportEmbed = originalMessage.embeds[0];
            const reportIdFooter = reportEmbed.footer.text.split("#")[1];
    
            const mentionedUser = extractMentionedUser(reportEmbed.description);
            if (mentionedUser) {
                const category = interaction.guild.channels.cache.get('1332000870681804830'); // ID de la categoría
                const channelName = `in-game-${reportIdFooter}`;

                const privateChannel = await interaction.guild.channels.create({
                    name: channelName,
                    type: 0, // Canal de texto
                    parent: category,
                    permissionOverwrites: [
                        {
                            id: interaction.guild.roles.everyone.id,
                            deny: ['ViewChannel'], // Bloquea la vista para todos
                        },
                        {
                            id: mentionedUser.id,
                            allow: ['ViewChannel', 'SendMessages', 'AttachFiles', 'ReadMessageHistory'], // Permisos específicos para el usuario mencionado
                            deny: ['MentionEveryone'], // Prevenir menciones de @everyone
                        },
                    ],
                });
                console.log(`Canal creado: ${privateChannel.name} (ID: ${privateChannel.id}) en la categoría ${category.name}`);
                console.log(`Player atendido: ${mentionedUser.tag} (ID: ${mentionedUser.id})`);

                const notifyEmbed = new EmbedBuilder()
                    .setTitle(`Reporte #${reportIdFooter} Tomado`)
                    .setDescription('¡Tu reporte ha sido tomado! Estaremos en contacto si necesitamos más información.')
                    .setColor('Yellow')
                    .setThumbnail('https://i.imgur.com/kwULhbl.png')
                    .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
                try {
                    await mentionedUser.send({ embeds: [notifyEmbed] });
                } catch {
                    console.log('El usuario mencionado tiene desactivados los mensajes directos.');
                }
            }
    
            const logChannel = interaction.client.channels.cache.get('1212423583825924146');
            const logEmbed = new EmbedBuilder()
                .setTitle(`Reporte #${reportIdFooter} Tomado`)
                .setDescription(`${reportEmbed.description}\n\n<:staff:1331986276521349141> ${staffRole} ${staffMember}`) // Añadiendo emoji, rango y mención del staff
                .setColor('Yellow')
                .setThumbnail(staffMember.displayAvatarURL())
                .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
            await logChannel.send({ embeds: [logEmbed] });
    
            // Crear nueva fila de botones con "Cerrar Reporte" habilitado y "Rechazar Reporte" deshabilitado
            const actionRow = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId(`close_report_${reportId}`)
                    .setLabel('Cerrar Reporte')
                    .setStyle(ButtonStyle.Success),
                new ButtonBuilder()
                    .setCustomId(`reject_report_${reportId}`)
                    .setLabel('Rechazar Reporte')
                    .setStyle(ButtonStyle.Danger)
                    .setDisabled(true) // Deshabilitar botón de "Rechazar Reporte"
            );
    
            await interaction.update({
                content: `Reporte tomado por ${staffMember}.`,
                components: [actionRow],
            });
        } catch (error) {
            console.error('Error al tomar el reporte:', error);
            await interaction.reply({ content: 'Hubo un error al intentar procesar el reporte.', ephemeral: true });
        }
    }

    // Botón "Cerrar Reporte"
    else if (action === 'close') {
        const reportOwnerId = procesados.get(reportId);
    
        if (reportOwnerId !== staffMember.id) {
            await interaction.reply({
                content: 'Solo el miembro del staff que tomó este reporte puede cerrarlo.',
                ephemeral: true,
            });
            return;
        }
    
        try {
            const originalMessage = await interaction.channel.messages.fetch(reportId);
            const reportEmbed = originalMessage.embeds[0];
            const reportIdFooter = reportEmbed.footer.text.split("#")[1];
    
            const mentionedUser = extractMentionedUser(reportEmbed.description);
            if (mentionedUser) {
                // Eliminar canal privado
                const privateChannel = interaction.guild.channels.cache.find(
                    (channel) => channel.name === `in-game-${reportIdFooter}`
                );

                if (privateChannel) {
                    await privateChannel.delete(`Cerrando el reporte #${reportIdFooter}`);
                    console.log(`Canal eliminado: ${privateChannel.name} (ID: ${privateChannel.id})`);

                }

                const notifyEmbed = new EmbedBuilder()
                    .setTitle(`Reporte #${reportIdFooter} Cerrado`)
                    .setDescription('¡Tu reporte ha sido cerrado! Gracias por tu contribución.')
                    .setColor('Green')
                    .setThumbnail('https://i.imgur.com/krv57l5.png')
                    .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
                try {
                    await mentionedUser.send({ embeds: [notifyEmbed] });
                } catch {
                    console.log('El usuario mencionado tiene desactivados los mensajes directos.');
                }
            }
    
            const logChannel = interaction.client.channels.cache.get('1212423583825924146');
            const logEmbed = new EmbedBuilder()
                .setTitle(`Reporte #${reportIdFooter} Cerrado`)
                .setDescription(`${reportEmbed.description}\n\n<:staff:1331986276521349141> ${staffRole} ${staffMember}`) // Incluyendo el rango y mención del staff
                .setColor('Green')
                .setThumbnail(staffMember.displayAvatarURL())
                .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
            await logChannel.send({ embeds: [logEmbed] });
    
            const disabledButton = new ButtonBuilder()
                .setCustomId(`close_report_${reportId}`)
                .setLabel('Reporte Cerrado')
                .setStyle(ButtonStyle.Success)
                .setDisabled(true);
    
            const updatedRow = new ActionRowBuilder().addComponents(disabledButton);
    
            await interaction.update({
                content: `Reporte cerrado por ${staffMember}.`,
                components: [updatedRow],
            });
    
            procesados.delete(reportId);
        } catch (error) {
            console.error('Error al cerrar el reporte:', error);
            await interaction.reply({ content: 'Hubo un error al intentar cerrar el reporte.', ephemeral: true });
        }
    }
    

    // Botón "Rechazar Reporte"
    else if (action === 'reject') {
        try {
            const originalMessage = await interaction.channel.messages.fetch(reportId);
            const reportEmbed = originalMessage.embeds[0];
            const reportIdFooter = reportEmbed.footer.text.split("#")[1];
    
            const mentionedUser = extractMentionedUser(reportEmbed.description);
            if (mentionedUser) {
                const notifyEmbed = new EmbedBuilder()
                    .setTitle(`Reporte #${reportIdFooter} Rechazado`)
                    .setDescription('Tu reporte ha sido rechazado. Si tienes más información, por favor crea un nuevo reporte.')
                    .setColor('Red')
                    .setThumbnail('https://i.imgur.com/lXqJtDF.png')
                    .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
                try {
                    await mentionedUser.send({ embeds: [notifyEmbed] });
                } catch {
                    console.log('El usuario mencionado tiene desactivados los mensajes directos.');
                }
            }
    
            const logChannel = interaction.client.channels.cache.get('1212423583825924146');
            const logEmbed = new EmbedBuilder()
                .setTitle(`Reporte #${reportIdFooter} Rechazado`)
                .setDescription(`<:staff:1331986276521349141> ${staffRole} ${staffMember}`) // Añadiendo emoji, rango y mención del staff
                .setColor('Red')
                .setThumbnail(staffMember.displayAvatarURL())
                .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
            await logChannel.send({ embeds: [logEmbed] });
    
            const disabledButton = new ButtonBuilder()
                .setCustomId(`reject_report_${reportId}`)
                .setLabel('Reporte Rechazado')
                .setStyle(ButtonStyle.Danger)
                .setDisabled(true);
    
            const updatedRow = new ActionRowBuilder().addComponents(disabledButton);
    
            await interaction.update({
                content: `El reporte ha sido rechazado por ${staffMember}.`,
                components: [updatedRow],
            });
    
            procesados.delete(reportId);
        } catch (error) {
            console.error('Error al rechazar el reporte:', error);
            await interaction.reply({ content: 'Hubo un error al intentar rechazar el reporte.', ephemeral: true });
        }
    }
    
});


// Login del bot
client.login(process.env.DISCORD_TOKEN);
