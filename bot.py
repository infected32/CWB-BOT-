import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import time
import os
from datetime import datetime

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
canal_abrir_caixa = 1309181452595757077
canal_rank = 1309181411751886869
canal_premio = 1222717244170174588

last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

# Emojis de reação
reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

# Ajuste das chances: Aumentando "SEM SORTE" e reduzindo itens raros
prizes = [
    {"name": "AK47", "image": "https://i.postimg.cc/KYWdMknH/Ak47.webp", "chance": 1, "description": "Uma poderosa AK47, perfeita para o apocalipse."},
    {"name": "VIP", "image": "https://i.postimg.cc/P537gpF5/pngtree-vip-3d-golden-word-element-png-image-240239.png", "chance": 0.01, "description": "Status VIP, benefícios exclusivos!"},
    {"name": "GIROCÓPTERO", "image": "https://i.postimg.cc/fR84MgkZ/Gyrocopter-Placeable.webp", "chance": 0.5, "description": "Girocóptero para viagens aéreas seguras."},
    {"name": "MOTO", "image": "https://i.postimg.cc/9f060tq9/Motorcycle-Placeable.webp", "chance": 0.8, "description": "Uma moto resistente para terrenos hostis."},
    {"name": "SEM SORTE", "image": "https://i.postimg.cc/Y0KZd5DN/DALL-E-2024-11-21-15-18-18-The-same-post-apocalyptic-supply-crate-marked-with-CWB-now-open-reve.webp", "chance": 92, "description": "A sorte não está do seu lado hoje."},
    {"name": "CWB Coin", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.1, "description": "CWB Coin, troque por vantagens raras."},
    {"name": "Eraser T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.1, "description": "Eraser T5, arma potente para apagar ameaças."},
    {"name": "BullDog T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.1, "description": "BullDog T5, espingarda implacável."},
    {"name": "Pack 5k Munição 9mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.5, "description": "5k munição 9mm urânio, poder de fogo intenso."},
    {"name": "Pack 5k Munição 762mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.5, "description": "5k munição 7.62mm urânio, destruição garantida."},
    {"name": "Pack 5k Munição Shot Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.5, "description": "5k munição Shot urânio, impacto devastador."}
]

mensagens_sem_sorte = [
    "O apocalipse não perdoa... nada hoje, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Tente outra vez!",
    "O vento soprou contra você desta vez. Não desista!",
    "A devastação venceu hoje... mas o amanhã te espera!",
]

mensagens_com_sorte = [
    "Você surpreendeu os mortos e saiu vencedor! Ganhou: **{prize}**.",
    "A sorte sorriu para você! **{prize}** agora é seu.",
    "Em meio ao caos, um presente raro: **{prize}**!",
    "Contra todas as probabilidades, você obteve **{prize}**!",
]

# Mensagens extras de interação
mensagens_extras = [
    "O Meu criador Wl observa do horizonte e dá um sorriso.",
    "Os espíritos do apocalipse aplaudem sua conquista.",
    "Um corvo pousa perto e parece respeitar sua vitória.",
    "As ruínas ao redor parecem menos sombrias agora."
]

def tempo_restante(last_time):
    return max(0, 10800 - (time.time() - last_time))

def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

def contar_raros(user_id):
    if user_id not in player_prizes:
        return 0
    return sum(1 for p in player_prizes[user_id] if p != "SEM SORTE")

# Status rotativo
status_list = [
    "Jogando 7 Days to Die",
    "Falando com Willi",
    "Conversando com Willi",
    "Dormindo"
]
status_index = 0

@tasks.loop(minutes=5)
async def mudar_status():
    global status_index
    await bot.change_presence(activity=discord.Game(name=status_list[status_index]))
    status_index = (status_index + 1) % len(status_list)

@tasks.loop(hours=7)
async def limpar_rank():
    player_prizes.clear()
    player_box_opens.clear()
    channel = bot.get_channel(canal_rank)
    embed = discord.Embed(
        title="⚡ Zeração de Ranking ⚡",
        description="O ranking foi zerado. Todos os prêmios e caixas foram resetados!",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)

@bot.event
async def on_ready():
    limpar_rank.start()
    mudar_status.start()
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def ajuda(ctx):
    ajuda_texto = """
    **Comandos disponíveis:**

    `!abrir_caixa` - Abra uma caixa no canal correto.
    `!abrir_admin` - Criador/autorizado podem abrir sem cooldown.
    `!limpar_chat` - Limpa 100 mensagens (admin).
    `!ajuda` - Esta mensagem de ajuda.
    `!rank_premios` - Ranking dos melhores prêmios.
    `!rank_caixas_abertas` - Ranking de caixas abertas.
    """
    embed = discord.Embed(
        title="Comandos Disponíveis",
        description=ajuda_texto,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def limpar_chat(ctx):
    if not ctx.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="Acesso Negado",
            description="Você não tem permissão para isso.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    deleted = await ctx.channel.purge(limit=100)
    embed = discord.Embed(
        title="Limpeza de Chat",
        description=f"Foram limpas {len(deleted)} mensagens.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, delete_after=5)

@bot.command()
async def abrir_caixa(ctx):
    if ctx.channel.id != canal_abrir_caixa:
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"{ctx.author.mention}, use este comando em <#{canal_abrir_caixa}>",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    user = ctx.author
    if user.id in last_attempt_time:
        tempo_rest = tempo_restante(last_attempt_time[user.id])
        if tempo_rest > 0:
            horas = int(tempo_rest // 3600)
            minutos = int((tempo_rest % 3600) // 60)
            segundos = int(tempo_rest % 60)
            embed = discord.Embed(
                title="Cooldown",
                description=f"{user.mention}, espere {horas}h {minutos}m {segundos}s para abrir outra caixa.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

    prize = escolher_premio()
    if prize["name"] == "SEM SORTE":
        mensagem = random.choice(mensagens_sem_sorte)
        desc = f"{ctx.author.mention}, {mensagem}"
    else:
        mensagem = random.choice(mensagens_com_sorte).format(prize=prize["name"])
        desc = f"{ctx.author.mention}, {mensagem}"
        player_prizes[user.id] = player_prizes.get(user.id, []) + [prize["name"]]

    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    embed = discord.Embed(
        title="🎁 Resultado da Caixa",
        description=desc,
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        # Reação extra e fala extra
        await msg.add_reaction("🎉")
        falas_extra = random.choice(mensagens_extras)
        raros = contar_raros(user.id)
        caixas_abertas = player_box_opens[user.id]
        parabens_msg = (f"🎉 **Parabéns {ctx.author.mention}!** Você ganhou: **{prize['name']}**!"
                        f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros: **{raros}**\n{falas_extra}")
        embed_parabens = discord.Embed(
            title="🥳 Ganhador do Sorteio!",
            description=parabens_msg,
            color=discord.Color.green()
        )
        embed_parabens.set_image(url=prize['image'])
        # Aviso em tempo real no canal de prêmios
        await bot.get_channel(canal_premio).send(embed=embed_parabens)

    last_attempt_time[user.id] = time.time()

@bot.command()
async def rank_premios(ctx):
    if ctx.channel.id != canal_rank:
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"Use este comando em <#{canal_rank}>",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    rank = sorted(player_prizes.items(), key=lambda x: sum(1 for p in x[1] if p != "SEM SORTE"), reverse=True)
    embed = discord.Embed(
        title="🏆 Ranking dos Melhores Prêmios",
        description="Top 10 jogadores com mais prêmios raros.",
        color=discord.Color.purple()
    )
    for i, (user_id, prizes) in enumerate(rank[:10], start=1):
        user = await bot.fetch_user(user_id)
        itens_raros = [p for p in prizes if p != "SEM SORTE"]
        valor = f"**Prêmios Raros:** {len(itens_raros)}"
        if itens_raros:
            valor += f"\n{', '.join(itens_raros)}"
        embed.add_field(
            name=f"{i}. {user.display_name}",
            value=valor,
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def rank_caixas_abertas(ctx):
    if ctx.channel.id != canal_rank:
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"Use este comando em <#{canal_rank}>",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    rank = sorted(player_box_opens.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(
        title="📦 Ranking de Abertura de Caixas",
        description="Top 5 jogadores que mais abriram caixas.",
        color=discord.Color.purple()
    )
    for i, (user_id, opens) in enumerate(rank[:5], start=1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.display_name}",
            value=f"**Caixas Abertas:** {opens}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def abrir_admin(ctx):
    criador_id = 470628393272999948
    usuario_autorizado_id = 434531832097144852

    if ctx.author.id not in [criador_id, usuario_autorizado_id]:
        embed = discord.Embed(
            title="Acesso Negado",
            description="Somente o criador ou usuário autorizado podem usar este comando.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Entre em contato com o criador para mais informações.")
        button = Button(label="Entrar em Contato", style=discord.ButtonStyle.link, url="https://discord.com/users/470628393272999948")
        view = View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)
        return

    prize = escolher_premio()
    player_box_opens[ctx.author.id] = player_box_opens.get(ctx.author.id, 0) + 1
    if prize["name"] != "SEM SORTE":
        player_prizes[ctx.author.id] = player_prizes.get(ctx.author.id, []) + [prize["name"]]

    desc = f"**{ctx.author.mention}** ganhou: **{prize['name']}**!"
    embed = discord.Embed(
        title="🎁 Caixa Especial Aberta!",
        description=desc,
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        await msg.add_reaction("🎉")
        raros = contar_raros(ctx.author.id)
        caixas_abertas = player_box_opens[ctx.author.id]
        falas_extra = random.choice([
            "O Meu criador dá um aceno de aprovação.",
            "Você sente que os espíritos do apocalipse te apoiam.",
            "Um silêncio respeitoso cai sobre as ruínas, reconhecendo seu feito.",
            "Até os corvos parecem impressionados."
        ])
        parabens_msg = (f"🎉 **Parabéns {ctx.author.mention}!** Você ganhou: **{prize['name']}**!"
                        f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros: **{raros}**\n{falas_extra}")
        embed_parabens = discord.Embed(
            title="🥳 Ganhador do Sorteio (Admin)!",
            description=parabens_msg,
            color=discord.Color.green()
        )
        embed_parabens.set_image(url=prize['image'])
        await bot.get_channel(canal_premio).send(embed=embed_parabens)

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
