import keep_alive
from discord.ext import commands
import threading
import discord
import asyncio
import aiohttp
import random
import socket
import ctypes
import time
import json
import ssl
import re
import os

token = ''
prefix = '/'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, case_insensitive=True, intents=intents)
bot.remove_command('help')

bots_channel = 123456789

threads = 500 + 4
queue = []

administrator_ids = []
administrator_roles = []

roles = {
    'role id': '50', # @everyone
    'role id 2': '50', # +50
    'role id 3': '50' # Booster
}

database = {}
invites_database = {}

async def update_database():
    with open('database.json', 'w') as f:
        json.dump(database, f)

async def update_invites(guild):
    invites = await guild.invites()
    invites_database[f'{guild.id}'] = [tuple((invite.code, invite.uses)) for invite in invites]

@bot.event
async def on_invite_create(invite):
    await update_invites(invite.guild)

@bot.event
async def on_invite_delete(invite):
    await update_invites(invite.guild)

@bot.event
async def on_member_join(member):
    inviter = None
    guild = member.guild
    guild_invites = await guild.invites()
    for guild_invite in guild_invites:
        try:
            for invite in invites_database.get(f'{guild.id}'):
                if invite[0] == guild_invite.code:
                    if int(guild_invite.uses) > invite[1]:
                        inviter = str(guild_invite.inviter.id)
                        database[f'{guild.id}'][f'{inviter}']['invites'] += 1
                        await update_database()
                        break
        except:
            pass
    await update_invites(guild)
    if f'{member.id}' not in database[f'{guild.id}'].keys():
        database[f'{guild.id}'][f'{member.id}'] = {'invites': 0, 'inviter': f'{inviter}'}
        await update_database()
    elif f'{member.id}' in database[f'{guild.id}'].keys():
        invites = database[f'{guild.id}'][f'{member.id}']['invites']
        database[f'{guild.id}'][f'{member.id}'] = {'invites': int(invites), 'inviter': f'{inviter}'}
        await update_database()
    channel = await bot.fetch_channel(bots_channel)
    if database[f'{guild.id}'][f'{member.id}']['inviter'] != None and inviter:
        invites = database[f'{guild.id}'][inviter]['invites']
        _50 = discord.utils.get(guild.roles, name='+50')
        _inviter = await guild.fetch_member(int(inviter))
        if invites >= 3 and _50 not in _inviter.roles:
            await _inviter.add_roles(_50)
        embed = discord.Embed(color=16083729, description=f'<@{member.id}> has joined! Invited by <@{inviter}> ({invites} invite' + ('s)' if invites != 1 else ')'))
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        await channel.send(embed=embed)
    else:
        embed = discord.Embed(color=16083729, description=f'<@{member.id}> has joined!')
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    guild = member.guild
    if database[f'{guild.id}'][f'{member.id}']['inviter'] is not None:
        inviter = str(database[f'{guild.id}'][f'{member.id}']['inviter'])
        database[f'{guild.id}'][inviter]['invites'] -= 1
        await update_database()
    await update_invites(guild)
    channel = await bot.fetch_channel(bots_channel)
    if database[f'{guild.id}'][f'{member.id}']['inviter'] is not None:
        invites = database[f'{guild.id}'][inviter]['invites']
        _50 = discord.utils.get(guild.roles, name='+50')
        _inviter = await guild.fetch_member(int(inviter))
        if invites < 3 and _50 in _inviter.roles:
            await _inviter.remove_roles(_50)
        embed = discord.Embed(color=16083729, description=f'<@{member.id}> has left! Invited by <@{inviter}> ({invites} invite' + ('s)' if invites != 1 else ')'))
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        await channel.send(embed=embed)
    else:
        embed = discord.Embed(color=16083729, description=f'<@{member.id}> has left!')
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if f'{message.author.id}' not in database[f'{message.guild.id}'].keys():
        database[f'{message.guild.id}'][f'{message.author.id}'] = {'invites': 0, 'inviter': None}
        await update_database()
    await bot.process_commands(message)

class tfollow_bot:

    def __init__(self, channel_id, amount):
        self.channel_id = str(channel_id)
        self.amount = int(amount)
        self.tokens = []
        self.load_tokens()
        random.shuffle(self.tokens)

    def load_tokens(self):
        self.tokens = open('tokens.txt', 'r').read().splitlines()

    def bot(self, i):
        try:
            _, _, token = self.tokens[i].split(':')
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
            origin = 'https://www.twitch.tv'
            content_type = 'text/plain;charset=UTF-8'
            client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
            authorization = f'OAuth {token}'
            accept_language = 'en-US'
            data = '[{"operationName":"FollowButton_FollowUser","variables":{"input":{"disableNotifications":false,"targetID":"%s"}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"3efee1acda90efdff9fef6e6b4a29213be3ee490781c5b54469717b6131ffdfe"}}}]' % self.channel_id
            content_length = len(data)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('gql.twitch.tv', 443))
                s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
                s.sendall(f'POST /gql HTTP/1.1\r\nHost: gql.twitch.tv\r\nAuthorization: {authorization}\r\nUser-Agent: {user_agent}\r\nOrigin: {origin}\r\nContent-Type: {content_type}\r\nClient-Id: {client_id}\r\nAccept-Language: {accept_language}\r\nContent-Length: {content_length}\r\n\r\n{data}\r\n'.encode('utf-8'))
                s.recv(4096)
        except:
            pass

    def start(self):
        for i in range(self.amount):
            while True:
                if threading.active_count() < threads:
                    threading.Thread(target=self.bot, args=(i,)).start()
                    break
        while True:
            if threading.active_count() == 4:
                break
        return

class tfriend_bot:

    def __init__(self, channel_id, amount):
        self.channel_id = str(channel_id)
        self.amount = int(amount)
        self.tokens = []
        self.load_tokens()
        random.shuffle(self.tokens)

    def load_tokens(self):
        self.tokens = open('tokens.txt', 'r').read().splitlines()

    def bot(self, i):
        try:
            _, _, token = self.tokens[i].split(':')
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
            origin = 'https://www.twitch.tv'
            content_type = 'text/plain;charset=UTF-8'
            client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
            authorization = f'OAuth {token}'
            accept_language = 'en-US'
            data = '[{"operationName":"FriendButton_CreateFriendRequest","variables":{"input":{"targetID":"%s"}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"380d8b19fcffef2fd8654e524444055dbca557d71968044115849d569d24129a"}}}]' % self.channel_id
            content_length = len(data)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('gql.twitch.tv', 443))
                s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
                s.sendall(f'POST /gql HTTP/1.1\r\nHost: gql.twitch.tv\r\nAuthorization: {authorization}\r\nUser-Agent: {user_agent}\r\nOrigin: {origin}\r\nContent-Type: {content_type}\r\nClient-Id: {client_id}\r\nAccept-Language: {accept_language}\r\nContent-Length: {content_length}\r\n\r\n{data}\r\n'.encode('utf-8'))
                _ = s.recv(4096).decode('utf-8')
                resp = s.recv(4096).decode('utf-8')
                if 'service error' in resp:
                    self.bot(i)
        except:
            pass

    def start(self):
        for i in range(self.amount):
            while True:
                if threading.active_count() < threads:
                    threading.Thread(target=self.bot, args=(i,)).start()
                    break
        while True:
            if threading.active_count() == 4:
                break
        return

def zoom():
    while True:
        try:
            task = queue.pop(0).split('|')
            if task[0] == 'tfollow':
                tfollow_bot(task[1], task[2]).start()
            elif task[0] == 'tfriend':
                tfriend_bot(task[1], task[2]).start()
        except:
            pass

threading.Thread(target=zoom).start()

async def status():
    while True:
        try:
            members = sum([len([member for member in guild.members if not member.bot]) for guild in bot.guilds])
            activity = discord.Activity(type=discord.ActivityType.watching, name=f'{members} members!')
            await bot.change_presence(activity=activity)
            await asyncio.sleep(300)
        except:
            pass

@bot.event
async def on_ready():
    bot.loop.create_task(status())
    try:
        with open('database.json', 'r') as f:
            global database
            database = json.load(f)
    except:
        open('database.json', 'a')
    for guild in bot.guilds:
        await update_invites(guild)
        if f'{guild.id}' not in database.keys():
            database[f'{guild.id}'] = {}
            await update_database()

@bot.event
async def on_command_error(ctx, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.delete()
    elif isinstance(error, commands.MissingRequiredArgument):
        ctx.command.reset_cooldown(ctx)
        embed = discord.Embed(color=16083729, description='You are missing arguments required to run this command!')
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        if ctx.channel.id == bots_channel: await ctx.send(embed=embed) 
    elif isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(color=16083729, description=f'{error}')
        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
        if ctx.channel.id == bots_channel: await ctx.send(embed=embed) 
    else:
        await ctx.message.delete()

@bot.command()
async def help(ctx):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}help')
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            embed = discord.Embed(color=16083729)
            embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
            embed.add_field(name='Help', value=f'`{bot.command_prefix}help`', inline=True)
            embed.add_field(name='Ticket', value=f'`{bot.command_prefix}ticket`', inline=True)
            embed.add_field(name='Close', value=f'`{bot.command_prefix}close`', inline=True)
            admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
            if admin_roles or ctx.author.id in administrator_ids:
                embed.add_field(name='Clear', value=f'`{bot.command_prefix}clear`', inline=True)
                embed.add_field(name='Update Database', value=f'`{bot.command_prefix}updatedb`', inline=True)
            embed.add_field(name='Twitch Info', value=f'`{bot.command_prefix}tinfo (channel)`', inline=True)
            embed.add_field(name='Twitch Followers', value=f'`{bot.command_prefix}tfollow (channel)`', inline=True)
            embed.add_field(name='Twitch Friend Requests', value=f'`{bot.command_prefix}tfriend (channel)`', inline=True)
            embed.add_field(name='Roblox Info', value=f'`{bot.command_prefix}rinfo (user)`', inline=True)
            embed.add_field(name='Roblox Templates', value=f'`{bot.command_prefix}rget (asset)`', inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.message.delete()

@bot.command()
async def ticket(ctx):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}ticket')
    if ctx.channel.type != discord.ChannelType.private:
        channels = [str(channel) for channel in bot.get_all_channels()]
        if f'ticket-{ctx.author.id}' in channels:
            await ctx.message.delete()
        else:
            ticket_channel = await ctx.guild.create_text_channel(f'ticket-{ctx.author.id}')
            await ticket_channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
            await ticket_channel.set_permissions(ctx.author, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
            embed = discord.Embed(color=16083729, description=f'Please enter the reason for this ticket, type `{bot.command_prefix}close` if you want to close this ticket.')
            embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
            await ticket_channel.send(f'{ctx.author.mention}', embed=embed)
            await ctx.message.delete()

@bot.command()
async def close(ctx):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}close')
    if ctx.channel.type != discord.ChannelType.private:
        admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
        if ctx.channel.name == f'ticket-{ctx.author.id}':
            await ctx.channel.delete()
        elif admin_roles and 'ticket' in ctx.channel.name or ctx.author.id in administrator_ids and 'ticket' in ctx.channel.name:
            await ctx.channel.delete()
        else:
            await ctx.message.delete()

@bot.command()
async def clear(ctx):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}clear')
    if ctx.channel.type != discord.ChannelType.private:
        admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
        if admin_roles or ctx.author.id in administrator_ids:
            await ctx.channel.purge(limit=None)
            await ctx.send(':zap:')
        else:
            await ctx.message.delete()

@bot.command()
async def updatedb(ctx):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}updatedb')
    if ctx.channel.type != discord.ChannelType.private:
        admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
        if admin_roles or ctx.author.id in administrator_ids:
            counter = 0
            members = [member for member in ctx.guild.members if not member.bot]
            for member in members:
                if f'{member.id}' not in database[f'{ctx.guild.id}'].keys():
                    database[f'{ctx.guild.id}'][f'{member.id}'] = {'invites': 0, 'inviter': None}
                    await update_database()
                    counter += 1
            embed = discord.Embed(color=16083729, description=(f'`{counter}` users added to database!' if counter != 1 else f'`{counter}` user added to database!'))
            embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
            await ctx.send(embed=embed)
        else:
            await ctx.message.delete()

@bot.command()
async def tinfo(ctx, channel):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}tinfo {channel}')
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        channel_lower = channel.lower()
                        headers = {
                            'Client-Id': 'abe7gtyxbr7wfcdftwyi9i5kej3jnq',
                            'Accept': 'application/vnd.twitchtv.v5+json'
                        }
                        async with session.get(f'https://api.twitch.tv/kraken/users?login={channel_lower}', headers=headers) as r:
                            r = await r.json()
                            channel_id = r['users'][0]['_id']
                        async with session.get(f'https://api.twitch.tv/kraken/channels/{channel_id}', headers=headers) as r:
                            r = await r.json()
                            name = r['display_name']
                            followers = r['followers']
                            views = r['views']
                            logo = r['logo']
                    except:
                        embed = discord.Embed(color=16083729, description=f'Invalid twitch channel!')
                        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                        await ctx.send(embed=embed)
                        return
                embed = discord.Embed(color=16083729)
                embed.set_thumbnail(url=f'{logo}')
                embed.add_field(name='Name', value=f'`{name}`', inline=True)
                embed.add_field(name='Channel ID', value=f'`{channel_id}`', inline=True)
                embed.add_field(name='Followers', value=f'`{followers}`', inline=True)
                embed.add_field(name='Channel Views', value=f'`{views}`', inline=True)
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(color=16083729, description='An error has occured while attempting to run this command!')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
        else:
            await ctx.message.delete()

@bot.command()
@commands.cooldown(1, 300, type=commands.BucketType.user)
async def tfollow(ctx, channel, amount: int=None):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}tfollow {channel}' + (f' {amount}' if amount else ''))
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            try:
                max_amount = 0
                member_roles = [role.id for role in ctx.author.roles]
                for role in member_roles:
                    if f'{role}' in roles.keys():
                        max_amount += int(roles[f'{role}'])
                member = ctx.guild.get_member(ctx.author.id)
                for status in member.activities:
                    if isinstance(status, discord.CustomActivity):
                        if status.name == 'zoom':
                            max_amount += 25
                            break
                admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
                if admin_roles or ctx.author.id in administrator_ids:
                    tfollow.reset_cooldown(ctx)
                    max_amount = len(open('tokens.txt', 'r').read().splitlines())
                if not amount:
                    amount = max_amount
                elif amount > max_amount:
                    amount = max_amount
                async with aiohttp.ClientSession() as session:
                    try:
                        channel_lower = channel.lower()
                        headers = {
                            'Client-Id': 'abe7gtyxbr7wfcdftwyi9i5kej3jnq',
                            'Accept': 'application/vnd.twitchtv.v5+json'
                        }
                        async with session.get(f'https://api.twitch.tv/kraken/users?login={channel_lower}', headers=headers) as r:
                            r = await r.json()
                            channel_id = r['users'][0]['_id']
                    except:
                        tfollow.reset_cooldown(ctx)
                        embed = discord.Embed(color=16083729, description=f'Invalid twitch channel!')
                        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                        await ctx.send(embed=embed)
                        return
                position = len(queue) + 1
                embed = discord.Embed(color=16083729, description=f'Sending `{amount}` twitch followers to `{channel}`! (`{position}/{position}`)')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
                queue.append(f'tfollow|{channel_id}|{amount}')
            except:
                tfollow.reset_cooldown(ctx)
                embed = discord.Embed(color=16083729, description='An error has occured while attempting to run this command!')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
        else:
            tfollow.reset_cooldown(ctx)
            await ctx.message.delete()

@bot.command()
@commands.cooldown(1, 300, type=commands.BucketType.user)
async def tfriend(ctx, channel, amount: int=None):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}tfriend {channel}' + (f' {amount}' if amount else ''))
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            try:
                max_amount = 0
                member_roles = [role.id for role in ctx.author.roles]
                for role in member_roles:
                    if f'{role}' in roles.keys():
                        max_amount += int(roles[f'{role}'])
                member = ctx.guild.get_member(ctx.author.id)
                for status in member.activities:
                    if isinstance(status, discord.CustomActivity):
                        if status.name == 'zoom':
                            max_amount += 25
                            break
                admin_roles = [role for role in ctx.author.roles if role.id in administrator_roles]
                if admin_roles or ctx.author.id in administrator_ids:
                    tfriend.reset_cooldown(ctx)
                    max_amount = len(open('tokens.txt', 'r').read().splitlines())
                if not amount:
                    amount = max_amount
                elif amount > max_amount:
                    amount = max_amount
                async with aiohttp.ClientSession() as session:
                    try:
                        channel_lower = channel.lower()
                        headers = {
                            'Client-Id': 'abe7gtyxbr7wfcdftwyi9i5kej3jnq',
                            'Accept': 'application/vnd.twitchtv.v5+json'
                        }
                        async with session.get(f'https://api.twitch.tv/kraken/users?login={channel_lower}', headers=headers) as r:
                            r = await r.json()
                            channel_id = r['users'][0]['_id']
                    except:
                        tfriend.reset_cooldown(ctx)
                        embed = discord.Embed(color=16083729, description=f'Invalid twitch channel!')
                        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                        await ctx.send(embed=embed)
                        return
                position = len(queue) + 1
                embed = discord.Embed(color=16083729, description=f'Sending `{amount}` twitch friend requests to `{channel}`! (`{position}/{position}`)')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
                queue.append(f'tfriend|{channel_id}|{amount}')
            except:
                tfriend.reset_cooldown(ctx)
                embed = discord.Embed(color=16083729, description='An error has occured while attempting to run this command!')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
        else:
            tfriend.reset_cooldown(ctx)
            await ctx.message.delete()

@bot.command()
async def rinfo(ctx, *, user):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}rinfo {user}')
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        try:
                            user = int(user)
                        except:
                            async with session.get(f'http://api.roblox.com/users/get-by-username?username={user}') as r:
                                r = await r.json()
                                user = r['Id']
                        async with session.get(f'https://api.roblox.com/users/{user}') as r:
                            r = await r.json()
                            name = r['Username']
                        async with session.get(f'https://friends.roblox.com/v1/users/{user}/followers/count') as r:
                            r = await r.json()
                            followers = r['count']
                        async with session.get(f'https://thumbnails.roblox.com/v1/users/avatar-headshot?format=Png&isCircular=false&size=420x420&userIds={user}') as r:
                            r = await r.json()
                            img = r['data'][0]['imageUrl']
                    except:
                        embed = discord.Embed(color=16083729, description=f'Invalid roblox user!')
                        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                        await ctx.send(embed=embed)
                        return
                embed = discord.Embed(color=16083729)
                embed.set_thumbnail(url=f'{img}')
                embed.add_field(name='Username', value=f'`{name}`', inline=True)
                embed.add_field(name='User ID', value=f'`{user}`', inline=True)
                embed.add_field(name='Followers', value=f'`{followers}`', inline=True)
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(color=16083729, description='An error has occured while attempting to run this command!')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
        else:
            await ctx.message.delete()

@bot.command()
async def rget(ctx, asset):
    print(f'{ctx.author} | {ctx.author.id} -> {bot.command_prefix}rget {asset}')
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.channel.id == bots_channel or ctx.author.id in administrator_ids:
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f'https://assetdelivery.roblox.com/v1/asset?id={asset}') as r:
                            r = await r.text()
                        async with session.get(f'https://assetdelivery.roblox.com/v1/asset?id=' + re.search('id=(.*)</url>', r).group(1)) as r:
                            r = await r.read()
                        with open(f'{asset}.png', 'wb') as f:
                            f.write(r)
                        embed = discord.Embed(color=16083729)
                        file = discord.File(f'{asset}.png')
                        embed.set_image(url=f'attachment://{asset}.png')
                        await ctx.send(embed=embed, file=file)
                    except:
                        embed = discord.Embed(color=16083729, description=f'Invalid roblox asset!')
                        embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                        await ctx.send(embed=embed)
                        return
                    finally:
                        try:
                            os.remove(f'{asset}.png')
                        except:
                            pass
            except:
                embed = discord.Embed(color=16083729, description='An error has occured while attempting to run this command!')
                embed.set_thumbnail(url='https://i.imgur.com/0Tvz0G2.png')
                await ctx.send(embed=embed)
        else:
            await ctx.message.delete()
keep_alive.keep_alive()
bot.run(token)
