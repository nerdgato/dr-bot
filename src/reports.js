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
    
    if (!message.channel.name.startsWith('in-game-')) return;

    
    const staffRole = message.member.roles.highest; 
    if (!staffRole) return;

    
    const mentionedUsers = message.mentions.users;
    if (mentionedUsers.size > 0) {
        for (const [userId, user] of mentionedUsers) {
            
            const channel = message.channel;
            await channel.permissionOverwrites.edit(userId, {
                SendMessages: true,
                AttachFiles: true
            });

            console.log(`Permiso de enviar mensajes habilitado para ${user.tag} en el canal ${channel.name}.`);
        }
    }
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

    
    const staffRole = interaction.member.roles.highest;

    
    const extractMentionedUser = async (content) => {
        const mentionRegex = /<@!?(\d+)>/;
        const match = content.match(mentionRegex);
        if (match) {
            const userId = match[1];
            try {
                const user = await client.users.fetch(userId);
                return user;
            } catch (error) {
                console.error(`Error al obtener el usuario ${userId}:`, error);
                return null;
            }
        } else {
            console.log('No se encontró una mención en el contenido:', content);
            return null;
        }
    };


    
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
    
            const mentionedUser = await extractMentionedUser(reportEmbed.description);

            if (mentionedUser) {
                const category = interaction.guild.channels.cache.find((c) => c.name === "TICKETS" && c.type === 4 
                );

                if (!category) {
                    console.error("La categoría no existe. Asegúrate de crearla antes.");
                    return interaction.reply({ content: "No se encontró la categoría para asignar este canal.", ephemeral: true });
                }

                const channelName = `in-game-${reportIdFooter}`;
                const privateChannel = await interaction.guild.channels.create({
                    name: channelName,
                    type: 0, 
                    parent: category.id, 
                    permissionOverwrites: [
                        {
                            id: interaction.guild.roles.everyone.id,
                            deny: ['ViewChannel'], 
                        },
                        {
                            id: mentionedUser.id,
                            allow: ['ViewChannel', 'ReadMessageHistory'], 
                            deny: ['SendMessages', 'MentionEveryone', 'AddReactions', 'CreatePublicThreads', 'CreatePrivateThreads', 'CreateInstantInvite', 'SendPolls'], // Denegar enviar mensajes
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
                .setDescription(`${reportEmbed.description}\n\n<:staff:1331986276521349141> ${staffRole} ${staffMember}`) 
                .setColor('Yellow')
                .setThumbnail(staffMember.displayAvatarURL())
                .setFooter({ text: 'BOUKENCRAFT TEAM' });
    
            await logChannel.send({ embeds: [logEmbed] });
    
            
            const actionRow = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId(`close_report_${reportId}`)
                    .setLabel('Cerrar Reporte')
                    .setStyle(ButtonStyle.Success),
                new ButtonBuilder()
                    .setCustomId(`reject_report_${reportId}`)
                    .setLabel('Rechazar Reporte')
                    .setStyle(ButtonStyle.Danger)
                    .setDisabled(true) 
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



client.login(process.env.DISCORD_TOKEN);
