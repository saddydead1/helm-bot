#!/usr/bin/env python3

import enum
import discord
import mcrcon
import configparser
import helmPlayerDb
import helmGuildDb
from discord import app_commands
from discord.ext import commands
import re
import traceback

# read config.ini
configuration = configparser.ConfigParser()
configuration.read('config.ini')
token = configuration.get('DISCORD', 'token')
rconIp = configuration.get('RCON', 'ip')
# rconPort = configuration.get('RCON', 'port')
rconPassword = configuration.get('RCON', 'password')
channelId = configuration.get('DISCORD', 'channelId')
roleId = configuration.get('DISCORD', 'roleId')
guildAdmRole = configuration.get('DISCORD', 'guildAdminRole')

# connect RCON
rcon = mcrcon.MCRcon(rconIp, rconPassword)
rcon.connect()

# connect Postgres
helmPlayerDb.createTable()
helmGuildDb.createTable()


# color discord and minecraft
class Color(enum.StrEnum):
    def __new__(cls, value, code, minecode):
        member = str.__new__(cls, value)
        member._value_ = value
        member.code = code
        member.minecode = minecode
        return member

    Black = 'black', 0x000000, "&0"
    DarkBlue = 'dark_blue', 0x0000AA, "&1"
    DarkGreen = 'dark_green', 0x00AA00, "&2"
    DarkAqua = 'dark_aqua', 0x00AAAA, "&3"
    DarkRed = 'dark_red', 0xAA0000, "&4"
    DarkPurple = 'dark_purple', 0xAA00AA, "&5"
    Gold = 'gold', 0xFFAA00, "&6"
    Gray = 'gray', 0xAAAAAA, "&7"
    DarkGray = 'dark_gray', 0x555555, "&8"
    Blue = 'blue', 0x5555FF, "&9"
    Green = 'green', 0x55FF55, "&a"
    Aqua = 'aqua', 0x55FFFF, "&b"
    Red = 'red', 0xFF5555, "&c"
    LightPurple = 'light_purple', 0xFF55FF, "&d"
    Yellow = 'yellow', 0xFFFF55, "&e"
    White = 'white', 0xFFFFFF, "&f"


class Role(str, enum.Enum):
    Leader = 'LEADER'
    Member = 'MEMBER'
    #CoLeader = 'CO-LEADER'  #пока не вижу смысла


# command prefix
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())


# start bot
@bot.event
async def on_ready():
    print('Helm is starting')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)


# /register
@bot.tree.command(name="register")
async def register(interaction: discord.Interaction, nickname: str, password: str):
    if interaction.channel.id == int(channelId):
        member = interaction.user
        user_id = member.id
        try:
            result = re.findall(r'^[\w.-]+$', password)
            if result:
                reg = rcon.command(f'nlogin register {nickname} {password}')
                print(reg)
                helmPlayerDb.addPlayer(nickname, user_id)
                await interaction.response.send_message(f"Аккаунт с ником '{nickname}' зарегистрирован! =)",
                                                        ephemeral=True)
                role = interaction.guild.get_role(int(roleId))
                await member.add_roles(role)
            else:
                await interaction.response.send_message(f"Нельзя использовать специальные символы в пароле!!",
                                                        ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{nickname}, вы уже зарегистрированы! =(", ephemeral=True)
            print(e)


# /changepass
@bot.tree.command(name="changepass")
async def changepass(interaction: discord.Interaction, newpassword: str):
    if interaction.channel.id == int(channelId):
        try:
            member = interaction.user
            user_id = member.id
            try:
                nickname = helmPlayerDb.getMinecraftNick(user_id)
                change = rcon.command(f'nlogin changepassword {nickname} {newpassword}')
                print(change)
                await interaction.response.send_message("Ваш пароль успешно изменен!", ephemeral=True)
            except:
                await interaction.response.send_message("Вы не зарегистрированы", ephemeral=True)
        except Exception as e:
            print(e)


# группа '/guild'
guild = app_commands.Group(name='guild', description="Команды гильдий")
setGroup = app_commands.Group(name='set', description="Управление гильдией")
add = app_commands.Group(name='add', description='Добавить в гильдию')
remove = app_commands.Group(name='remove', description='Удаления в гильдии')


# /guild create БЕЗ ФЛАГА
@guild.command(name="create", description='Создать новую гильдию')
@discord.app_commands.checks.has_role(int(guildAdmRole))
async def guildCommands(interaction: discord.Interaction, name: str, displayname: str, color: Color):
    try:
        guild = interaction.guild
        await guild.create_role(name=displayname, colour=color.code)
        role = discord.utils.get(guild.roles, name=displayname)
        leader_role = await guild.create_role(name=f"Глава {displayname}", colour=color.code)
        leader_role_id = leader_role.id
        await guild.create_forum(name=f"{name}-форум",
                                 overwrites={guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                             role: discord.PermissionOverwrite(read_messages=True)})
        channel = discord.utils.get(guild.channels, name=f"{name}-форум")
        channel_id = channel.id
        role_id = role.id
        helmGuildDb.createGuild(name, displayname, color.value, channel_id, role_id, leader_role_id)
        create = rcon.command(f'team add {name} "{displayname}"')
        print(create)
        colourAdd = rcon.command(f'team modify {name} color {color.value}')
        print(colourAdd)
        create = rcon.command(f'luckperms creategroup {name}')
        print(create)
        prefix = rcon.command(f'luckperms group {name} permission set prefix.1.[{color.minecode}{name}&f]')
        await interaction.response.send_message(f"Гильдия {displayname} создана!", ephemeral=True)
    except Exception as e:
        print(e)
        await interaction.response.send_message("Error =( Проверьте правильность данных", ephemeral=True)


# /guild set leader
@setGroup.command(name='leader', description='Добавить главу гильдии')
@discord.app_commands.checks.has_role(int(guildAdmRole))
async def setLeader(interaction: discord.Interaction, name: discord.Member, guild: str):
    try:
        discordID = name.id
        displayname = helmGuildDb.getDisplayName(guild)
        if helmGuildDb.checkMember(discordID):
            if helmGuildDb.checkGuild(guild):
                helmGuildDb.addMember(discordID, guild, Role.Leader)
                command = rcon.command(f'team join {guild} {helmPlayerDb.getMinecraftNick(discordID)}')
                print(command)
                command = rcon.command(f'luckperms user {helmPlayerDb.getMinecraftNick(discordID)} parent add {guild}')
                print(command)
                await name.add_roles(interaction.guild.get_role(helmGuildDb.getLeaderRoleId(guild)))
                await interaction.response.send_message(f"Для гильдии {displayname} установлен глава {name}",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message("Гильдии не существует", ephemeral=True)
        else:
            await interaction.response.send_message("Error =(", ephemeral=True)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        await interaction.response.send_message("Error =( Проверьте правильность данных", ephemeral=True)


# /guild add player
@add.command(name='player', description='Добавить участника')
async def addPlayer(interaction: discord.Interaction, name: str, member: discord.Member, role: Role):
    try:
        if interaction.user.get_role(helmGuildDb.getLeaderRoleId(name)):
            if helmGuildDb.checkGuild(name):
                if not role == Role.Leader:
                    command = rcon.command(f'team join {name} {helmPlayerDb.getMinecraftNick(member.id)}')
                    print(command)
                    command = rcon.command(
                        f'luckperms user {helmPlayerDb.getMinecraftNick(member.id)} parent add {name}')
                    print(command)
                    helmGuildDb.addMember(member.id, name, role)
                    await member.add_roles(interaction.guild.get_role(helmGuildDb.getGuildRole(name)))
                    await interaction.response.send_message(
                        f'Игрок {member} добавлен в гильдию {helmGuildDb.getDisplayName(name)} с ролью {role.value}',
                        ephemeral=True)
                else:
                    await interaction.response.send_message(f'Вы не можете выдать роль {role.value}', ephemeral=True)
            else:
                await interaction.response.send_message("Гильдии не существует", ephemeral=True)
        else:
            await interaction.response.send_message('Вы не владелец гильдии!', ephemeral=True)
    except Exception as e:
        print(e)
        await interaction.response.send_message('Error =(', ephemeral=True)

# /guild remove player
@remove.command(name='player', description='Удалить из гильдии')
async def removePlayer(interaction: discord.Interaction, name: str, member: discord.Member):
    try:
        if interaction.user.get_role(helmGuildDb.getLeaderRoleId(name)):
            if not helmGuildDb.getRole(member.id) == Role.Leader:
                helmGuildDb.removePlayer(member.id)
                command = rcon.command(f'team leave {helmPlayerDb.getMinecraftNick(member.id)}')
                print(command)
                command = rcon.command(f'luckperms user {helmPlayerDb.getMinecraftNick(member.id)} remove add {name}')
                print(command)
                await interaction.response.send_message(f'Игрок {member} изгнан из гильдии {helmGuildDb.getDisplayName(name)}!', ephemeral=True)
            else:
                await interaction.response.send_message('Вы не глава гильдии', ephemeral=True)
    except Exception as e:
        print(e)

# /guild remove guild
@remove.command(name="guild", description='Удалить гильдию')
@discord.app_commands.checks.has_role(int(guildAdmRole))
async def guildCommands(interaction: discord.Interaction, name: str):
    try:
        guild = interaction.guild
        role = guild.get_role(helmGuildDb.getGuildRole(name))
        leaderRole = guild.get_role(helmGuildDb.getLeaderRoleId(name))
        channel = guild.get_channel(helmGuildDb.getForum(name))
        await channel.delete()
        await role.delete()
        await leaderRole.delete()
        helmGuildDb.removeGuild(name)
        command = rcon.command(f'team remove {name}')
        print(command)
        command = rcon.command(f'luckperms deletegroup {name}')
        print(command)
        await interaction.response.send_message(f"Гильдия удалена!", ephemeral=True)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await interaction.response.send_message("Error =(", ephemeral=True)


guild.add_command(setGroup)
guild.add_command(add)
guild.add_command(remove)
bot.tree.add_command(guild)

# connect
bot.run(token)
