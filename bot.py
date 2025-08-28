import discord
from discord import app_commands
import yt_dlp
import os

TOKEN = os.environ.get("TOKEN")

# Configuración de yt_dlp y FFmpeg
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Clase del cliente y árbol de comandos
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} se ha conectado y está listo!')
    print(f'Sincronizados {len(await client.tree.fetch_commands())} comandos.')

# --- COMANDOS ACTUALIZADOS ---

@client.tree.command(name="disconnect", description="Desconecta el bot del canal de voz.")
async def salir(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("¡Desconectado del canal de voz!")
    else:
        await interaction.response.send_message("El bot no está en un canal de voz.", ephemeral=True)

@client.tree.command(name="play", description="Reproduce una canción (se conecta automáticamente).")
@app_commands.describe(busqueda="La URL de YouTube o el nombre de la canción a buscar.")
async def reproducir(interaction: discord.Interaction, busqueda: str):
    # Paso 1: Comprobar si el usuario está en un canal de voz.
    if not interaction.user.voice:
        await interaction.response.send_message("Debes estar en un canal de voz para usar este comando.", ephemeral=True)
        return

    # Deferir la respuesta para tener más tiempo de procesar todo.
    await interaction.response.defer()

    # Paso 2: Obtener el cliente de voz del servidor (si existe).
    voice_client = interaction.guild.voice_client
    
    # Paso 3: Si el bot no está conectado, se conecta al canal del usuario.
    if not voice_client:
        channel = interaction.user.voice.channel
        voice_client = await channel.connect() # Conecta y actualiza la variable voice_client

    # Si ya está reproduciendo algo, lo detenemos para la nueva canción.
    if voice_client.is_playing():
        voice_client.stop()

    try:
        # Paso 4: Buscar y obtener la información del video.
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{busqueda}", download=False)['entries'][0]
            audio_url = info['url']
        
        # Paso 5: Reproducir el audio.
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source)
        
        # Enviamos el mensaje de confirmación.
        await interaction.followup.send(f"**Reproduciendo ahora:** {info['title']}")

    except Exception as e:
        await interaction.followup.send(f"Ocurrió un error al intentar reproducir la canción: {e}")

# Ejecutar el bot
client.run(TOKEN)
