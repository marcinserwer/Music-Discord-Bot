import discord

def create_embed(title, url, thumbnail, duration):
    embed = discord.Embed(description="", color=1412061)
    embed.set_thumbnail(url=thumbnail)
    embed.add_field(name="I play:", value=f"[{title}]({url})", inline=False)
    embed.add_field(name="Song length:", value=duration, inline=False)

    return embed