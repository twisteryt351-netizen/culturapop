import os
import random
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURACOES ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID_POP")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

for nome, valor in [
    ("GROQ_API_KEY", GROQ_API_KEY),
    ("BLOGGER_ID_POP", BLOGGER_ID),
    ("BLOGGER_CLIENT_ID", CLIENT_ID),
    ("BLOGGER_CLIENT_SECRET", CLIENT_SECRET),
    ("BLOGGER_REFRESH_TOKEN", REFRESH_TOKEN),
]:
    if not valor:
        raise ValueError(f"Faltou configurar a variavel/segredo: {nome}")

groq_client = Groq(api_key=GROQ_API_KEY)
MODELO_IA = "llama-3.3-70b-versatile"

# --- LISTA BASE DE CULTURA POP (Eterna e Reutilizável) ---
TEMAS = [
    # --- ANIMES & MANGÁS ---
    "o anime e mangá 'Akira' (1988)",
    "o anime 'Yu Yu Hakusho' e sua passagem pelo Brasil",
    "a saga de 'Dragon Ball Z' e o legado de Akira Toriyama",
    "o anime 'Neon Genesis Evangelion'",
    "o mangá e anime 'Berserk' de Kentaro Miura",
    "o anime clássico 'Speed Racer'",
    "o anime 'Cowboy Bebop'",
    "o mangá e anime 'Monster' de Naoki Urasawa",
    "a franquia 'Sailor Moon'",
    "o anime 'Death Note'",
    "o anime 'Os Cavaleiros do Zodíaco'",
    "o filme 'A Viagem de Chihiro' e o Studio Ghibli",
    "o anime e filme 'Ghost in the Shell' (1995)",
    "o anime 'Fullmetal Alchemist: Brotherhood'",
    "o mangá e anime 'One Piece'",
    "o anime 'Hunter x Hunter'",
    "o anime 'Serial Experiments Lain'",
    "o mangá 'Vagabond' de Takehiko Inoue",
    "o anime 'InuYasha'",
    "o mangá e anime de basquete 'Slam Dunk'",

    # --- GAMES & CONSOLES ---
    "o jogo RPG 'Chrono Trigger'",
    "o jogo 'Castlevania: Symphony of the Night'",
    "a guerra de consoles dos anos 90 (Super Nintendo vs Mega Drive)",
    "o jogo 'Resident Evil 1' (1996) e o Survival Horror",
    "o jogo 'Final Fantasy VII' (PS1)",
    "o jogo 'The Legend of Zelda: Ocarina of Time'",
    "o console 'PlayStation 1' e a revolução da Sony",
    "o jogo de terror 'Silent Hill 2'",
    "o jogo 'GTA San Andreas'",
    "a franquia 'Pokémon' na era do Game Boy (Red/Blue)",
    "o jogo indie 'Hollow Knight'",
    "a criação e o impacto do mascote 'Sonic the Hedgehog'",
    "o jogo 'Super Mario 64'",
    "o jogo de corrida 'Top Gear' (SNES)",
    "o fenômeno 'Minecraft'",
    "o jogo 'Shadow of the Colossus'",
    "a franquia de luta 'Street Fighter II'",
    "a franquia 'Metal Gear Solid' de Hideo Kojima",
    "o jogo 'Half-Life 2'",
    "o console 'Dreamcast' e o fim da era SEGA em hardware",

    # --- CINEMA & SÉRIES ---
    "o filme 'Jurassic Park' (1993)",
    "a trilogia de filmes 'O Senhor dos Anéis'",
    "o filme 'De Volta para o Futuro'",
    "o filme 'Blade Runner' (1982)",
    "o filme 'Pulp Fiction' de Quentin Tarantino",
    "o filme '2001: Uma Odisséia no Espaço'",
    "o filme de terror 'O Exorcista' (1973)",
    "a trilogia clássica de 'Star Wars' (Episódios IV, V e VI)",
    "o filme 'Matrix' (1999)",
    "a série de TV 'Breaking Bad'",
    "a sitcom 'Seinfeld'",
    "o programa e série 'Chaves'",
    "o filme 'O Iluminado' de Stanley Kubrick",
    "a série 'Twin Peaks' de David Lynch",
    "o filme 'Alien: O Oitavo Passageiro' (1979)",
    "a trilogia de filmes 'O Poderoso Chefão'",
    "a franquia de terror 'A Hora do Pesadelo' (Freddy Krueger)",
    "o filme 'Clube da Luta'",
    "a série 'The Sopranos'",
    "o filme brasileiro 'Cidade de Deus'",

    # --- MÚSICA & BANDAS ---
    "o álbum 'Dark Side of the Moon' do Pink Floyd",
    "a trajetória da banda de metal 'Iron Maiden'",
    "o movimento Grunge e a banda 'Nirvana'",
    "o álbum 'Thriller' e a carreira de Michael Jackson",
    "o festival 'Woodstock 1969'",
    "a banda 'Black Sabbath' e o nascimento do Heavy Metal",
    "o álbum 'Abbey Road' e o fim dos 'Beatles'",
    "o fenômeno global do K-Pop e a banda 'BTS'",
    "o show e festival 'Live Aid 1985'",
    "a carreira e os alter egos de 'David Bowie'",
    "o álbum 'Master of Puppets' do Metallica",
    "a trajetória da banda 'AC/DC'",
    "o festival 'Rock in Rio 1985' no Brasil",
    "o álbum 'OK Computer' do Radiohead",
    "a dupla de música eletrônica 'Daft Punk'",
    "a estética musical do Synthwave e anos 80",
    "a banda 'Led Zeppelin'",
    "a cena musical japonesa 'Visual Kei' (X Japan)",
    "a ascensão do 'Guns N' Roses' nos anos 90",
    "o movimento Punk de 1977 (Sex Pistols e Ramones)",

    # --- CARTOONS & QUADRINHOS ---
    "o desenho 'Coragem, o Cão Covarde'",
    "a animação 'Avatar: A Lenda de Aang'",
    "o desenho 'O Laboratório de Dexter'",
    "a animação 'Batman: A Série Animada' (1992)",
    "o desenho 'As Meninas Superpoderosas'",
    "o desenho clássico 'Caverna do Dragão'",
    "a animação 'Apenas um Show' (Regular Show)",
    "o desenho 'Hora de Aventura'",
    "o estúdio de animação 'Hanna-Barbera'",
    "a HQ e graphic novel 'Watchmen' de Alan Moore",
    "a HQ 'O Cavaleiro das Trevas' de Frank Miller",
    "as histórias em quadrinhos da 'Turma da Mônica'",
    "a HQ 'Sandman' de Neil Gaiman",
    "a saga de quadrinhos 'A Morte do Superman'",
    "a graphic novel 'Maus' sobre o Holocausto",
    "a saga 'Guerra Civil' da Marvel Comics",
    "a história em quadrinhos 'A Piada Mortal' (Coringa)",
    "o selo de quadrinhos adultos 'Vertigo' da DC",
    "a HQ 'V de Vingança'",
    "o desenho clássico do 'Pica-Pau' no Brasil"
]

ARQUIVO_HISTORICO = "historico_pop_resenha.txt"


def tema_ja_usado(tema):
    if not os.path.exists(ARQUIVO_HISTORICO):
        return False
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        linhas = f.read().splitlines()
    # Evita repetir o mesmo tema exato nos últimos 15 ciclos
    return tema in linhas[-15:]


def marcar_tema_usado(tema):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(tema + "\n")


def escolher_tema():
    disponiveis = [t for t in TEMAS if not tema_ja_usado(t)]
    if not disponiveis:
        disponiveis = TEMAS
    return random.choice(disponiveis)


IMAGEM_PADRAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png"


def buscar_imagem_openverse(palavra_chave):
    try:
        resposta = requests.get(
            "https://api.openverse.org/v1/images/",
            params={
                "q": palavra_chave,
                "license_type": "commercial",
                "page_size": 3,
                "mature": "false",
            },
            headers={"User-Agent": "RoboResenhaPop/1.0"},
            timeout=10,
        )
        resultados = resposta.json().get("results", [])
        return resultados[0]["url"] if resultados else IMAGEM_PADRAO
    except Exception as e:
        print(f"Erro ao buscar imagem: {e}")
        return IMAGEM_PADRAO


def gerar_tabela_imagem_blogger(url_img, alt_title):
    return (
        '<table align="center" cellpadding="0" cellspacing="0" '
        'class="tr-caption-container" style="margin-left: auto; margin-right: auto;">'
        '<tbody><tr><td style="text-align: center;">'
        f'<img alt="{alt_title}" border="0" height="360" src="{url_img}" '
        f'title="{alt_title}" width="640" /></td></tr></tbody></table><br />'
    )


def pedir_ia_groq(prompt, temperatura=0.7, max_tokens=None):
    kwargs = {
        "messages": [{"role": "user", "content": prompt}],
        "model": MODELO_IA,
        "temperature": temperatura,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    response = groq_client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def gerar_esqueleto(instrucao_tema):
    """ETAPA 1: Sorteia um ângulo e pede um esqueleto detalhado.
    A injeção do ângulo garante posts inéditos no futuro."""
    
    angulos = [
        "Foco em Bastidores e Desenvolvimento (como foi criado, perrengues de produção, equipe, segredos de criação).",
        "Análise Crítica e Temática (mensagens ocultas, filosofia, simbolismos, análise do roteiro ou estética).",
        "Impacto Cultural e Legado (como mudou a indústria, revolução no gênero, obras que foram influenciadas por ela).",
        "Curiosidades Pouco Conhecidas e Easter Eggs (fatos estranhos, detalhes imperceptíveis, mitos e verdades).",
        "Visão Nostálgica e Recepção no Brasil (exibição na TV aberta/locadoras, dublagem nacional, febre entre os fãs na época)."
    ]
    angulo_sorteado = random.choice(angulos)
    
    prompt = f"""
Você é um roteirista de documentários sobre cultura pop (animes, mangás, cartoons, séries, quadrinhos, música e games).

Tema central de hoje: {instrucao_tema}

⚠️ ÂNGULO OBRIGATÓRIO PARA A MATÉRIA DE HOJE:
"{angulo_sorteado}"

Primeiro, ANTES de escrever o artigo, monte um ESQUELETO detalhado guiado por esse ângulo:
- Confirme o tema principal e o ângulo escolhido.
- Liste de 5 a 7 tópicos/seções que o artigo vai cobrir.
- Para cada tópico, escreva 1-2 frases resumindo o que será abordado, SEM repetir informação.

Responda apenas com esse esqueleto, em texto simples (sem HTML).
"""
    return pedir_ia_groq(prompt, temperatura=0.6)


def gerar_artigo_completo(esqueleto):
    """ETAPA 2: Pede o artigo completo usando o esqueleto como guia obrigatório."""
    prompt = f"""
Você é um redator de cultura pop premiado, cronista! Escreve artigos estilo documentário/resenha
para um blog de fãs muito engajado. Escreva com MUITO capricho, sem pressa - este é um
artigo de destaque do blog. 
Reforçando: Você é um redator (pesquisa várias fontes) especializado em cultura pop (animes, mangás, quadrinhos, cartoons,
filmes, séries, games e música) para um blog de fãs engajado. Sabe todas as novidades, sabe traçar raciocínio, memória e transcrever de forma agradável, engraçada, futuca bastidores, sabe uma ou outra fofoquinha e constrói comunidade.

Use este esqueleto como guia OBRIGATÓRIO, desenvolvendo cada tópico dele em profundidade,
sem pular nenhum e sem repetir informação entre seções:

{esqueleto}

REGRAS DE CONTEÚDO:
- Baseie-se em fatos históricos e culturais reais sobre o tema. NÃO invente datas ou números sem certeza.
- Escreva de forma agradável e envolvente.
- PROIBIDO repetir a mesma frase ou ideia. Cada parágrafo deve avançar a narrativa.
- Tamanho OBRIGATÓRIO: no MÍNIMO 1400 palavras. Desenvolva bem cada seção.

REGRAS DE FORMATO (HTML puro, sem Markdown):
1. Comece direto com um parágrafo de abertura instigante (sem h1).
2. Cada tópico do esqueleto vira um subtítulo <h2> próprio.
3. Inclua PELO MENOS 2 notas do autor engraçadas e leves, cada uma dentro de <blockquote>, com comentários de fã.
4. Não inclua links no corpo do texto.
5. Termine com um parágrafo de fechamento reflexivo sobre o legado do tema.
"""
    return pedir_ia_groq(prompt, temperatura=0.75)


def gerar_titulo(esqueleto):
    prompt = (
        f"Baseado neste esqueleto de artigo:\n{esqueleto}\n\n"
        f"Crie um título de blog envolvente, nostálgico, otimizado para SEO, em português "
        f"do Brasil, sem aspas. Responda apenas o título, texto puro."
    )
    return pedir_ia_groq(prompt, temperatura=0.7).replace('"', '').strip()


def extrair_palavra_chave(esqueleto):
    prompt = (
        f"Baseado neste esqueleto de artigo:\n{esqueleto}\n\n"
        f"Dê apenas UMA palavra-chave em inglês que descreva visualmente o tema principal "
        f"(ex: 'anime', 'rock concert', 'retro cartoon', 'vintage video game'). "
        f"Responda só a palavra."
    )
    return pedir_ia_groq(prompt, temperatura=0.3).strip().lower().split()[0]


def gerar_cta():
    return """
<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
    <p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Gostou dessa viagem no tempo?</p>
    <p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Curta, deixe seu comentário contando suas lembranças do assunto e compartilhe com quem também vai se emocionar!</p>
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
        <a href="#" onclick="window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(document.title + ' - ' + window.location.href), '_blank'); return false;" style="background-color: #25d366; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">WhatsApp</a>
        <a href="#" onclick="window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #1877f2; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Facebook</a>
        <a href="#" onclick="window.open('https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #000; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">X</a>
    </div>
</div>
"""


def obter_credenciais():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


def publicar_no_blogger(titulo, conteudo, tags):
    creds = obter_credenciais()
    blogger = build('blogger', 'v3', credentials=creds)
    corpo_postagem = {
        'kind': 'blogger#post',
        'title': titulo,
        'content': conteudo,
        'labels': tags,
    }
    resultado = blogger.posts().insert(blogId=BLOGGER_ID, body=corpo_postagem).execute()
    print(f"Postado: '{titulo}' -> {resultado.get('url')}")


if __name__ == "__main__":
    print("Gerando resenha/documentario de cultura pop...")
    instrucao_tema = escolher_tema()
    print(f"Tema sorteado: {instrucao_tema}")

    esqueleto = gerar_esqueleto(instrucao_tema)
    print("Esqueleto e ângulo gerados. Escrevendo artigo completo...")

    corpo = gerar_artigo_completo(esqueleto)
    titulo = gerar_titulo(esqueleto)
    palavra_chave = extrair_palavra_chave(esqueleto)
    img_url = buscar_imagem_openverse(palavra_chave)
    img_html = gerar_tabela_imagem_blogger(img_url, titulo)
    cta = gerar_cta()

    aviso = (
        '<p style="font-size: 12px; color: #888; font-style: italic;">Artigo de caráter '
        'cultural, histórico e opinativo, com fins de entretenimento e nostalgia.</p>'
    )

    html_final = f"{img_html}{corpo}{cta}{aviso}"
    publicar_no_blogger(titulo, html_final, ["resenha", "documentario", "cultura pop"])
    marcar_tema_usado(instrucao_tema)
    print("Concluído com sucesso!")
