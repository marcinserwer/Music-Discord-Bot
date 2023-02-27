import os #Biblioteka do obsługi systemu operacyjnego
import discord #Biblioteka do obsługi Discord API
from discord.ext import commands #Biblioteka do obsługi komend Discorda
from dotenv import load_dotenv #Biblioteka do wczytywania zmiennych środowiskowych
import youtube_dl #Biblioteka do pobierania muzyki z YouTube
import asyncio #Biblioteka do asynchronicznej obsługi zadań

load_dotenv() #Umożliwia wczytywanie danych z .env
TOKEN = os.getenv('DISCORD_TOKEN') #Pobiera token bota z pliku .env

intents = discord.Intents.default()
intents.message_content = True #Umożliwia czytanie i pisanie na czacie 
client = commands.Bot(command_prefix="/", intents=intents)  #Komendy Discorda z prefiksem "/"


client.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'} #Ustawienia odtwarzacza FFMPEG
client.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'} #Ustawienia odtwarzacza FFMPEG
is_playing = False #Zmienna przechowująca True/False czy aktualnie gra muzyka
skip_playing = False #Zmienna przechowująca True/False czy aktualnie gra muzyka
queue = []  #Lista kolejek piosenek

@client.event #Funkcja wywoływana, gdy bot jest gotowy do użycia
async def on_ready(): 
    print(f'{client.user} has connected to Discord!')


@client.command(name="play", help="Plays a selected song from youtube") #Odtwarza utwory z podanego linku
async def play(ctx, url):
    global is_playing, queue, skip_playing

    if not is_playing: #Sprawdza czy piosenka jest grana
        is_playing = True
        if ctx.author.voice is None: #Sprawdza czy użytkownik jest połączony z kanałem
            await ctx.send("Musisz być połączony z kanałem głosowym, aby odtwarzać muzykę.")
            is_playing = False
            return
        
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        await ctx.send('Odtwarzam: '+url)

        guild = ctx.guild
        with youtube_dl.YoutubeDL(client.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            URL = info['formats'][0]['url']
            voice = discord.utils.get(client.voice_clients, guild=guild)
            if voice and voice.is_connected(): #Sprawdza czy bot jest na czacie głosowym
                await voice.move_to(ctx.author.voice.channel)
            else:
                voice = await ctx.author.voice.channel.connect()
            
            voice.play(discord.FFmpegPCMAudio(URL, **client.FFMPEG_OPTIONS))
            
            while voice.is_playing():
                await asyncio.sleep(1)
            is_playing = False
            if len(queue) > 0:
                next_song = queue.pop(0)  #Pobiera pierwszą piosenkę z kolejki
                skip_playing = False
                await play(ctx, next_song)  #Odtwarza muzykę
    else:
        queue.append(url)  #Dodaje nową piosenkę do kolejki
        if not skip_playing:
            await ctx.send('Dodano piosenkę do kolejki')


@client.command(name="stop") #Zatrzymuje aktualną odtwarzaną muzykę
async def stop(ctx):
    global is_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        is_playing = False
        await ctx.send('Odtwarzanie zatrzymane.')
    else:
        await ctx.send('Nie odtwarzam żadnej muzyki.')

@client.command(name="skip") #Odtwarza następną muzykę z listy
async def skip(ctx):
    global queue, skip_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        if len(queue) > 0:
            next_song = queue.pop(0)
            skip_playing = True
            await play(ctx, next_song)
        else:
            await ctx.send('Brak kolejnej piosenki na liście oczekujących.')
    else:
        await ctx.send('Nie odtwarzam żadnej muzyki.')


client.run(TOKEN)