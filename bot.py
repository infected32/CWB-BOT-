import discord
from discord.ext import commands, tasks
import random
import time
import os
from datetime import datetime

# Definindo intents necessários
intents = discord.Intents.default()
intents.messages = True  # Necessário para ler e reagir a mensagens
intents.guilds = True    # Necessário para interagir com guildas/servidores
intents.message_content = True  # Necessário para acessar o conteúdo das mensagens

# Criando o bot com os intents necessários
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
canal_abrir_caixa = 1309181452595757077  # Canal de comando para abrir caixas
canal_rank = 1309181411751886869  # Canal de Rank Automático
canal_admin = 1309181411751886869  # Canal onde apenas administradores podem digitar mensagens

# Dicionário para armazenar o último tempo de sorteio de cada jogador e pontuação de embers
last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

# Emojis de reação para adicionar
reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

# Lista de prêmios com links diretos das imagens
prizes = [
    {"name": "AK47", "image": "https://i.postimg.cc/KYWdMknH/Ak47.webp", "chance": 2},
    {"name": "VIP", "image": "https://i.postimg.cc/P537gpF5/pngtree-vip-3d-golden-word-element-png-image-240239.png", "chance": 0.001},
    {"name": "GIROCÓPTERO", "image": "https://i.postimg.cc/fR84MgkZ/Gyrocopter-Placeable.webp", "chance": 2},
    {"name": "MOTO", "image": "https://i.postimg.cc/9f060tq9/Motorcycle-Placeable.webp", "chance": 2},
    {"name": "SEM SORTE", "image": "https://i.postimg.cc/Y0KZd5DN/DALL-E-2024-11-21-15-18-18-The-same-post-apocalyptic-supply-crate-marked-with-CWB-now-open-reve.webp", "chance": 95},
]

# Mensagens de falha (Sem sorte)
mensagens_sem_sorte = [
    "O apocalipse não perdoa... o destino não sorriu para você hoje. Tente novamente, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Mas não desista, o amanhã pode ser mais favorável.",
    "Os ventos sombrios do CWB sopram contra você, mas continue tentando. A sorte pode mudar!",
    "A devastação não te favoreceu... mas continue lutando, a esperança é a última que morre.",
]

# Mensagens de sorte (quando o jogador ganha prêmios)
mensagens_com_sorte = [
    "O apocalipse não conseguiu te derrotar. A sorte está do seu lado, sobrevivente! Você ganhou: **{prize}**.",
    "Você desafiou os mortos e a sorte te recompensou. Prepare-se para sua próxima jornada!",
    "O CWB é implacável, mas hoje você venceu. Aproveite seu prêmio, herói do apocalipse!",
    "Em meio à destruição, você brilhou como um farol de esperança. O apocalipse não pode te parar!",
]

# Mensagens apocalípticas (para prêmios valiosos)
mensagens_apocalipticas = [
    "As nuvens negras se abrem, e o poder está ao seu alcance, {user}!",
    "Os espíritos do apocalipse sussurram seu nome... você foi escolhido, {user}!",
    "Hoje, os mortos levantaram-se para saudar {user}. A sorte está ao seu lado!",
    "Nas trevas do apocalipse, um brilho de esperança aparece para {user}.",
    "Você venceu o apocalipse e emergiu como um verdadeiro guerreiro, {user}!",
    "{user}, a devastação não é párea para sua sorte. Domine a vitória!",
    "Os ventos da destruição carregam seu nome, {user}. Hoje, você é imbatível!",
    "A terra treme sob seus pés, {user}, enquanto o apocalipse se curva diante de sua vitória!",
    "{user}, você foi agraciado pelas forças do além. Este é o seu dia de sorte!",
    "Com os olhos da noite sobre você, {user}, a fortuna finalmente lhe sorriu!"
]

# Comando de ajuda com imagem
@bot.command()
async def ajuda(ctx):
    ajuda_texto = """
    **Comandos disponíveis:**

    `!abrir_caixa` - Abra uma caixa para ganhar prêmios. Apenas pode ser usado no canal correto.
    `!abrir_admin` - Apenas o criador pode usar este comando, sem cooldown.
    `!limpar_chat` - Limpa o chat, só pode ser usado por administradores. (Comando de emergência)
    `!ajuda` - Exibe esta mensagem de ajuda.
    `!rank_premios` - Exibe o ranking dos melhores prêmios.
    `!rank_caixas_abertas` - Exibe o ranking dos jogadores que mais abriram caixas.
    
    **Nota:** O comando `!abrir_caixa` só pode ser usado no canal correto. Consulte o administrador para mais informações.
    """
    
    embed = discord.Embed(
        title="Comandos Disponíveis",
        description=ajuda_texto,
        color=discord.Color.blue()
    )
    # Definir a imagem do canal de ajuda fornecido
    embed.set_image(url="https://i.postimg.cc/rmt7CVjF/DALL-E-2024-11-21-15-22-03-A-rugged-survivor-in-a-post-apocalyptic-setting-wearing-worn-out-cloth.webp")
    
    await ctx.send(embed=embed)

# Função para selecionar um prêmio com base nas chances ajustadas
def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

# Comando para abrir a caixa com cooldown
@bot.command()
async def abrir_caixa(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_abrir_caixa:  
        await ctx.send(f"{ctx.author.mention}, você só pode usar o comando neste canal: <#{canal_abrir_caixa}>")
        return

    user = ctx.message.author

    # Verifica se o jogador já tentou nos últimos 3 horas
    if user.id in last_attempt_time:
        tempo_rest = tempo_restante(last_attempt_time[user.id])
        if tempo_rest > 0:
            horas = int(tempo_rest // 3600)
            minutos = int((tempo_rest % 3600) // 60)
            segundos = int(tempo_rest % 60)
            await ctx.send(f"{user.mention}, você precisa esperar {horas}h {minutos}m {segundos}s para tentar novamente.")
            return

    # Sorteia um prêmio com base nas chances ajustadas
    prize = escolher_premio()

    # Mensagem diferente dependendo se ganhou ou não
    if prize["name"] == "SEM SORTE":
        mensagem = random.choice(mensagens_sem_sorte)
    else:
        mensagem = random.choice(mensagens_com_sorte).format(prize=prize["name"])
        player_prizes[user.id] = player_prizes.get(user.id, []) + [prize["name"]]  # Armazena o prêmio

        # Envia uma mensagem apocalíptica mencionando o apelido do jogador para prêmios valiosos
        mensagem_apocaliptica = random.choice(mensagens_apocalipticas).format(user=user.display_name)
        await ctx.send(mensagem_apocaliptica)

    # Incrementa o contador de caixas abertas
    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    # Cria o embed com a imagem do prêmio ou da mensagem de azar
    embed = discord.Embed(
        title="🎁 Você abriu a Caixa de Presentes!",
        description=f"{user.mention}, {mensagem} Você ganhou: **{prize['name']}**!" if prize["name"] != "SEM SORTE" else f"{user.mention}, {mensagem}",
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])  # A imagem agora usa um link direto válido

    # Envia a mensagem com o embed no canal
    msg = await ctx.send(embed=embed)

    # Reage no post do prêmio valioso apenas
    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))

    # Atualiza o tempo da última tentativa do jogador
    last_attempt_time[user.id] = time.time()

# Comando para exibir o ranking dos prêmios (top 10)
@bot.command()
async def rank_premios(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return
    
    rank = sorted(player_prizes.items(), key=lambda x: sum(1 for prize in x[1] if prize != "SEM SORTE"), reverse=True)
    mensagem = "🏆 **Ranking dos Melhores Prêmios** 🏆\n\n"
    
    for i, (user_id, prizes) in enumerate(rank[:10], start=1):
        user = await bot.fetch_user(user_id)
        itens_raros = [p for p in prizes if p != "SEM SORTE"]
        mensagem += f"{i}. **{user.display_name}** - {len(itens_raros)} prêmios raros: {', '.join(itens_raros)}\n"
    
    await ctx.send(mensagem)

# Comando para exibir o ranking das caixas abertas (top 5)
@bot.command()
async def rank_caixas_abertas(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return
    
    rank = sorted(player_box_opens.items(), key=lambda x: x[1], reverse=True)
    mensagem = "📦 **Ranking de Abertura de Caixas** 📦\n\n"
    
    for i, (user_id, opens) in enumerate(rank[:5], start=1):
        user = await bot.fetch_user(user_id)
        mensagem += f"{i}. **{user.display_name}** - {opens} caixas abertas\n"
    
    await ctx.send(mensagem)

# Limpeza automática diária do chat (à meia-noite)
@tasks.loop(minutes=1)
async def limpar_chat_automatica():
    now = datetime.now()
    if now.hour == 0 and now.minute == 0:  # Exatamente à meia-noite
        channel = bot.get_channel(canal_rank)
        await channel.purge(limit=100)  # Limpa até 100 mensagens do canal
        embed = discord.Embed(
            title="⚡Limpeza Automática do Chat⚡",
            description="O apocalipse renovou o chat para um novo ciclo de destruição.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

        # Resetando os rankings (prêmios e caixas abertas)
        player_prizes.clear()
        player_box_opens.clear()

# Mudança de status do bot a cada 5 minutos
@tasks.loop(minutes=5)
async def mudar_status():
    status_list = [
        "Jogando 7 Days to Die",
        "Falando com Willi",
        "Explorando o apocalipse",
        "Sobrevivendo a um ataque zumbi",
        "Procurando a cura para a pandemia",
        "Desafiante do apocalipse"
    ]
    await bot.change_presence(activity=discord.Game(random.choice(status_list)))

# Rodando o bot com o token de ambiente
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
