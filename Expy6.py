import discord
from discord.ext import commands 
import yt_dlp
import asyncio
import random
import re

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_PATH = "C:/ffmpeg/ffmpeg-N-117673-gbb57b78013-win64-gpl/bin/ffmpeg.exe"  
FFMPEG_OPTIONS = {"executable": FFMPEG_PATH, "options": "-vn"}
YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You are not in a Voice channel.")
        if not ctx.voice_client:
            await voice_channel.connect()

        youtube_url_pattern = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:                
                    if youtube_url_pattern.match(search):                   
                        info = ydl.extract_info(search, download=False)
                    else:
                        info = ydl.extract_info(f"ytsearch:{search}", download=False)
                        if 'entries' in info:
                            info = info["entries"][0]

                    url = info["url"]
                    title = info["title"]
                    self.queue.append((url, title))
                    await ctx.send(f"Added to queue: **{title}**")

                except Exception as e:
                    await ctx.send("There was an error fetching the song.")
                    print(f"Error with yt_dlp: {e}")  

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def stop(self, ctx):
        """Stops playback and clears the queue."""
        if ctx.voice_client:
            self.queue.clear() 
            ctx.voice_client.stop() 
            await ctx.voice_client.disconnect() 
            await ctx.send("Stopped playback and cleared the queue.")

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles the current queue."""
        if not self.queue:
            return await ctx.send("The queue is empty, nothing to shuffle!")
        
        random.shuffle(self.queue)
        await ctx.send("The queue has been shuffled!")

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            try:
                source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
                await ctx.send(f"Now Playing: **{title}**")
            except Exception as e:
                await ctx.send("There was an error playing the song.")
                print(f"Error with FFmpeg or playback: {e}")  
                await ctx.voice_client.disconnect()
        else:
            await ctx.send("Queue is empty.")
            await ctx.voice_client.disconnect() 

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped")

client = commands.Bot(command_prefix="!", intents=intents)

async def main():
    await client.add_cog(MusicBot(client))
    await client.start("MTMwMDczMzI4ODA4Mzg4MjAwNA.Ggh4pF.6vb1l2AqeolqgCtsP1GAyzYSy91lDtd7duh8zw") 

asyncio.run(main())
