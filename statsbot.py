'''
MIT License

Copyright (c) 2017 grokkers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
import crasync
from discord.ext import commands
from ext.context import CustomContext
from ext import embeds
from collections import defaultdict
from contextlib import redirect_stdout
import datetime
import traceback
import asyncio
import aiohttp
import psutil
import time
import json
import sys
import os
import re
import inspect
import io
import textwrap

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''
    pass

class StatsBot(commands.AutoShardedBot):
    '''
    Custom Client for cr-statsbot - Made by verix#7220
    '''
    emoji_servers = [
        315043391081676810, 
        337918174475452426, 
        337919522163916815, 
        337975017469902848,
        ]

    developers = [
        273381165229146112,
        319395783847837696,
        180314310298304512
    ]

    def __init__(self):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasync.Client(self.session)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.remove_command('help')
        self.messages_sent = 0
        self.load_extensions()

    def get_cremojis(self):
        emojis = []
        for id in self.emoji_servers:
            g = self.get_guild(id)
            for e in g.emojis:
                emojis.append(e)
        return emojis

    def _add_commands(self):
        '''Adds commands automatically'''
        for name, attr in inspect.getmembers(self):
            if isinstance(attr, commands.Command):
                self.add_command(attr)

    def load_extensions(self, cogs=None, path='cogs.'):
        '''Loads the default set of extensions or a seperate one if given'''
        base_extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        for extension in cogs or base_extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'LoadError: {extension}\n'
                      f'{type(e).__name__}: {e}')

    @property
    def token(self):
        '''Returns your token wherever it is'''
        try:
            with open('data/config.json') as f:
                return json.load(f)['token'].strip('"')
        except FileNotFoundError:
            return None

    @classmethod
    def init(bot, token=None):
        '''Starts the actual bot'''
        bot = StatsBot()
        token = token or bot.token
        try:
            bot.run(token.strip('"'), bot=True, reconnect=True)
        except Exception as e:
            print('Error in starting the bot. Check your token.')

    def restart(self):
        '''Forcefully restart the bot.'''
        os.execv(sys.executable, ['python'] + sys.argv)

    async def get_prefix(self, message):
        '''Returns the prefix.

        Still need to do stuff with db to get server prefix.
        '''
        with open('data/guild.json') as f:
            cfg = json.load(f)

        id = str(message.guild.id)

        prefixes = [
            f'<@{self.user.id}> ', 
            f'<@!{self.user.id}> ',
            cfg.get(id, '#')
            ]

        return prefixes

    async def on_connect(self):
        '''
        Called when the bot has established a 
        gateway connection with discord
        '''
        print('----------------------------')
        print('StatsBot connected!')
        print('----------------------------')

        self._add_commands()
        # had to put this here due to an issue with the 
        # latencies property

    async def on_ready(self):
        '''
        Called when guild streaming is complete 
        and the client's internal cache is ready.
        '''
        print('StatsBot is ready!')
        print('----------------------------')
        print(f'Logged in as: {self.user}')
        print(f'Client ID: {self.user.id}')
        print('----------------------------')
        print(f'Guilds: {len(self.guilds)}')
        print(f'Users: {len(self.users)}')
        print('----------------------------')
        self.cremojis = self.get_cremojis()

    async def on_shard_ready(self, shard_id):
        '''
        Called when a shard has successfuly 
        connected to the gateway.
        '''
        print(f'Shard `{shard_id}` ready!')
        print('----------------------------')

    async def on_command(self, ctx):
        '''Called when a command is invoked.'''
        cmd = ctx.command.qualified_name.replace(' ', '_')
        self.commands_used[cmd] += 1

    async def process_commands(self, message):
        '''Utilises the CustomContext subclass of discord.Context'''
        ctx = await self.get_context(message, cls=CustomContext)
        if ctx.command is None:
            return
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        error_message = 'Player tags should only contain these characters:\n' \
                        '**Numbers:** 0, 2, 8, 9\n' \
                        '**Letters:** P, Y, L, Q, G, R, J, C, U, V'
        if isinstance(error, InvalidTag):
            await ctx.send(error_message)
        else:
            raise error

    async def on_message(self, message):
        '''Called when a message is sent/recieved.'''
        self.messages_sent += 1
        if message.author.bot:
            return 
        await self.process_commands(message)

    @commands.command()
    async def ping(self, ctx):
        """Pong! Returns average shard latency."""
        em = discord.Embed()
        em.title ='Pong! Websocket Latency: '
        em.description = f'{self.latency * 1000:.4f} ms'
        em.color = await ctx.get_dominant_color(self.user.avatar_url)
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)


    @commands.command()
    async def invite(self, ctx):
        """Returns the invite url for the bot."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.embed_links = True
        perms.attach_files = True
        perms.add_reactions = True
        await ctx.send(f'**Invite link:** \n<{discord.utils.oauth_url(self.user.id, perms)}>')

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix):
        '''Change the bot prefix for your server.'''
        id = str(ctx.guild.id)
        g_config = ctx.load_json('data/guild.json')
        g_config[id] = prefix
        ctx.save_json(g_config, 'data/guild.json')
        await ctx.send(f'Changed the prefix to: `{prefix}`')

    @commands.command(aliases=['about'])
    async def bot(self, ctx):
        '''Shows information and stats about the bot.'''
        em = discord.Embed()
        em.timestamp = datetime.datetime.utcnow()
        status = str(ctx.guild.me.status)
        if status == 'online':
            em.set_author(name="Stats", icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name="Stats", icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name="Stats", icon_url='https://i.imgur.com/dCLTaI3.png')
            em.color = discord.Color.red()

        total_online = len({m.id for m in self.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.users)
        channels = sum(1 for g in self.guilds for _ in g.channels)

        now = datetime.datetime.utcnow()
        delta = now - self.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt
        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)
        saved_tags = len(ctx.load_json())
        g_authors = 'verixx, fourjr, kwugfighter, FloatCobra, XAOS1502'
        em.description = 'StatsBot by verixx, kwugfighter and fourjr. Join the support server [here](https://discord.gg/maZqxnm).'

        em.add_field(name='Current Status', value=str(status).title())
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name='Latency', value=f'{self.latency*1000:.2f} ms')
        em.add_field(name='Guilds', value=len(self.guilds))
        em.add_field(name='Members', value=f'{total_online}/{total_unique} online')
        em.add_field(name='Channels', value=f'{channels} total')
        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name='RAM Usage', value=f'{memory_usage:.2f} MiB')
        em.add_field(name='CPU Usage',value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name='Commands Run', value=sum(self.commands_used.values()))
        em.add_field(name='Saved Tags', value=saved_tags)
        em.add_field(name='Github', value='[Click Here](https://github.com/grokkers/cr-statsbot)')
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.embed_links = True
        perms.attach_files = True
        perms.add_reactions = True
        em.add_field(name='Invite', value=f'[Click Here]({discord.utils.oauth_url(self.user.id, perms)})')
        em.set_footer(text=f'Bot ID: {self.user.id}')

        await ctx.send(embed=em)

    @commands.command()
    async def help(self, ctx):
        """Shows the help message."""
        em = discord.Embed(color=embeds.random_color())

        prefix = ctx.prefix

        if ctx.message.mentions:
            if ctx.prefix.strip() == ctx.message.mentions[0].mention:
                prefix = '#'

        for cmd in sorted(self.commands, key=lambda x: x.cog_name):
            em.add_field(
                        name=f'{prefix+cmd.signature}', 
                        value=cmd.short_doc, 
                        inline=False
                        )

        em.title = '`Stats - Help`'
        em.description = 'Here is a list of commands you can use with this bot. ' \
                         'Join the [support server here](https://discord.gg/maZqxnm) ' \
                         'if you are having any issues.'
        em.set_thumbnail(url=self.user.avatar_url)
        await ctx.send(embed=em)

    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates python code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            #'_': self._last_result,
            'source': inspect.getsource
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()
        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            return await err.add_reaction('\u2049')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if self.token in value:
                value = value.replace(self.token,"[EXPUNGED]")
            if ret is None:
                if value:
                    try:
                        out = await ctx.send(f'```py\n{value}\n```')
                    except:
                        paginated_text = ctx.paginate(value)
                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                out = await ctx.send(f'```py\n{page}\n```')
                                break
                            await ctx.send(f'```py\n{page}\n```')
            else:
                self._last_result = ret
                try:
                    out = await ctx.send(f'```py\n{value}{ret}\n```')
                except:
                    paginated_text = ctx.paginate(f"{value}{ret}")
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            out = await ctx.send(f'```py\n{page}\n```')
                            break
                        await ctx.send(f'```py\n{page}\n```')

        if out:
            await out.add_reaction('\u2705') #tick
        if err:
            await err.add_reaction('\u2049') #x

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

if __name__ == '__main__':
    StatsBot.init()