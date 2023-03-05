import os #Operating system library
import discord #Library to support the Discord API
from discord.ext import commands #Discord command library
from dotenv import load_dotenv #Library for loading environment variables
import youtube_dl #Library for downloading music from YouTube
import asyncio #Library for asynchronous task handling
from message import create_embed #Import of the function that creates the text to be displayed

load_dotenv() #Allows you to load data from .env
TOKEN = os.getenv('DISCORD_TOKEN') #Gets the bot token from the .env file

intents = discord.Intents.default()
intents.message_content = True #Allows you to read and write in chat 
client = commands.Bot(command_prefix="/", intents=intents) #Discord commands with "/" prefix


client.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'} #FFMPEG player settings
client.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'} #FFMPEG player settings
is_playing = False #A variable that stores True/False whether music is currently playing
skip_playing = False #A variable that stores True/False whether music is omitted
queue = []  #Song queue list

@client.event #Function called when the bot is ready to use
async def on_ready(): 
    print(f'{client.user} has connected to discord!')


@client.command(name="play", help="Plays the selected song from YouTube") #Plays songs from the given link
async def play(ctx, *args):
    global is_playing, queue, skip_playing
    url = " ".join(args) 

    if not is_playing: #Checks if the bot is currently playing music
        is_playing = True
        if ctx.author.voice is None: #Checks if the user is connected to the channel
            await ctx.send("You must be connected to a voice channel to play music.")
            is_playing = False
            return
        
        if ctx.voice_client is None: #Checks if the bot is already connected to the voice channel
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        guild = ctx.guild
        with youtube_dl.YoutubeDL(client.YDL_OPTIONS) as ydl:
            if "http" in url: #Checks whether the user provided a link or a name
                info = ydl.extract_info(url, download=False) #Searching for a song by URL
            else:
                search_results = ydl.extract_info(f"ytsearch:{url}", download=False) #Search for a song using text
                url = search_results['entries'][0]['webpage_url'] #Selects the first search result
                info = ydl.extract_info(url, download=False) #Retrieves information about a song using a URL
                
            title = info.get('title', None)
            thumbnail = info.get('thumbnail', None)
            duration = info.get('duration', None)

            duration_minutes = int(duration / 60)
            duration_seconds = int(duration % 60)
            duration_formatted = "{:d}:{:02d}".format(duration_minutes, duration_seconds)

            embed = create_embed(title, url, thumbnail, duration_formatted)

            await ctx.send(embed=embed)

            URL = info['formats'][0]['url']
            voice = discord.utils.get(client.voice_clients, guild=guild)
            if voice and voice.is_connected(): #Checks if the bot is in voice chat
                await voice.move_to(ctx.author.voice.channel)
            else:
                voice = await ctx.author.voice.channel.connect()
            
            voice.play(discord.FFmpegPCMAudio(URL, **client.FFMPEG_OPTIONS))
            
            while voice.is_playing():
                await asyncio.sleep(1)
            is_playing = False
            if len(queue) > 0:
                next_song = queue.pop(0) #Fetches the first song in the queue
                skip_playing = False
                await play(ctx, next_song) #Plays music
    else:
        queue.append(url) #Adds a new song to the queue
        if not skip_playing:
            await ctx.send('Added a song to the queue.')


@client.command(name="stop", help="Stops the currently playing music") #Stops the currently playing music
async def stop(ctx):
    global is_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing(): #Checks if a song is playing
        voice.stop()
        is_playing = False
        await ctx.send('Playback stopped.')
    else:
        await ctx.send("I don't play any music.")

@client.command(name="skip", help="Plays the next song in the list") #Plays the next music in the list
async def skip(ctx):
    global queue, skip_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing(): #Checks if a song is playing
        voice.stop()
        if len(queue) > 0: #Checks if there is a track in the queue
            next_song = queue.pop(0)
            skip_playing = True
            await play(ctx, next_song)
        else:
            await ctx.send('There is no next song on the waiting list.')
    else:
        await ctx.send("I don't play any music.")


client.run(TOKEN)