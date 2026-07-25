import os
import random
import feedparser
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURAÇÕES ---
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

# --- FONTES: nacionais e internacionais de cultura pop (incluindo games) ---
FONTES = {
    # Nacionais
    "Jbox": "https://jbox.com.br/feed/",
    "Omelete": "https://www.omelete.com.br/sitemap-news.xml",
    "Jovem Nerd": "https://jovemnerd.com.br/feed-completo",
    "Critical Hits": "https://criticalhits.com.br/feed/",
    "IGN Brasil": "https://br.ign.com/feed/",
    "Legiao dos Herois": "https://legiaodosherois.com.br/feed/",
    "AnimeNew": "https://www.animenew.com.br/feed/",
    "Adrenaline (Games)": "https://www.adrenaline.com.br/feed/",
    "TecMundo Games": "https://www.tecmundo.com.br/feed/games",

    # Internacionais - anime/manga/geek
    "Anime News Network": "https://www.animenewsnetwork.com/all/rss.xml",
    "Otaku USA": "https://otakuusamagazine.com/feed/",
    "CBR": "https://www.cbr.com/feed/",
    "Screen Rant": "https://screenrant.com/feed/",
    "Crunchyroll News": "https://www.crunchyroll.com/newsrss",

    # Internacionais - filmes/series
    "Variety": "https://variety.com/feed/",
    "Deadline": "https://deadline.com/feed/",

    # Internacionais - games
    "IGN Global": "https://www.ign.com/feed",
    "Kotaku": "https://kotaku.com/rss",
    "GameSpot": "https://www.gamespot.com/feeds/mashup/",

    # Musica (rock, pop, k-pop, j-pop)
    "NME": "https://www.nme.com/feed",
    "Soompi (K-pop)": "https://www.soompi.com/feed",
    "Rolling Stone": "https://www.rollingstone.com/feed/",
    "Pitchfork": "https://pitchfork.com/rss/news/",
}

# --- Tags/labels do Blogger por categoria (a IA escolhe a categoria certa) ---
CATEGORIAS_TAGS = {
    "anime": ["anime", "cultura pop", "japao"],
    "manga": ["manga", "cultura pop", "japao"],
    "cartoon": ["cartoon", "animacao", "cultura pop"],
    "quadrinho": ["quadrinhos", "hq", "cultura pop"],
    "filme": ["filme", "cinema", "cultura pop"],
    "serie": ["serie", "streaming", "cultura pop"],
    "game": ["games", "jogos", "cultura pop"],
    "musica": ["musica", "k-pop", "j-pop", "rock", "cultura pop"],
}

ARQUIVO_HISTORICO = "historico_pop_novidades.txt"


def ja_foi_postada(link):
    if not os.path.exists(ARQUIVO_HISTORICO):
        return False
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return link in f.read()


def marcar_como_postada(link):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def pegar_novidade():
    fontes_lista = list(FONTES.items())
    random.shuffle(fontes_lista)

    for nome_fonte, url_rss in fontes_lista:
        try:
            feed = feedparser.parse(url_rss, agent="Mozilla/5.0")
            if feed.bozo and not feed.entries:
                print(f"Fonte com problema: {nome_fonte} -> {url_rss}")
                continue
        except Exception as e:
            print(f"Fonte falhou: {nome_fonte} -> {url_rss} | Erro: {e}")
            continue

        for entrada in feed.entries[:5]:
            link = entrada.get("link")
            titulo = entrada.get("title")
            resumo = entrada.get("summary") or entrada.get("description") or ""

            if not link or not titulo:
                continue

            if not ja_foi_postada(link):
                print(f"Novidade encontrada em {nome_fonte}: {titulo[:60]}...")
                return titulo, resumo, link, nome_fonte

    return None, None, None, None


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
            headers={"User-Agent": "RoboCulturaPop/1.0"},
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


def pedir_ia_groq(prompt, temperatura=0.7):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODELO_IA,
        temperature=temperatura,
    )
    return response.choices[0].message.content.strip()


def extrair_palavra_chave(titulo):
    prompt = (
        f"Baseado neste titulo: '{titulo}', de apenas UMA palavra-chave em ingles que "
        f"descreva visualmente o tema (ex: 'anime', 'kpop concert', 'superhero movie', "
        f"'video game', 'rock band'). Responda so a palavra."
    )
    return pedir_ia_groq(prompt, temperatura=0.3).strip().lower().split()[0]


def identificar_categoria(titulo):
    categorias_validas = list(CATEGORIAS_TAGS.keys())
    prompt = (
        f"Baseado neste titulo de noticia: '{titulo}', escolha a categoria mais adequada "
        f"entre: {', '.join(categorias_validas)}. Responda APENAS com a palavra da categoria."
    )
    resposta = pedir_ia_groq(prompt, temperatura=0.2).strip().lower()
    for cat in categorias_validas:
        if cat in resposta:
            return cat
    return "anime"


def gerar_titulo(titulo_original):
    prompt = (
        f"Crie um titulo inedito, chamativo, otimizado para SEO, em portugues do Brasil, "
        f"sem aspas, baseado nesta noticia de cultura pop: '{titulo_original}'. "
        f"Responda apenas o titulo, texto puro."
    )
    return pedir_ia_groq(prompt, temperatura=0.7).replace('"', '').strip()


def gerar_artigo(titulo_original, resumo, nome_fonte):
    prompt = f"""
Voce e um redator(pesquisa varias fontes) especializado em cultura pop (animes, mangas, quadrinhos, cartoons,
filmes, series, games e musica - rock, pop, k-pop, j-pop, metal) para um blog de fas muito
engajado. Sabe todas as novidades, sabe traçar raciocinio memoria e transcrever de forma agradavel,engraçada, futuca bastidores, sabe uma ou outra fofoquinha, sabe contruir comunidade, Escreva com qualidade alta, sem pressa - capriche de verdade.

Traduza e reescreva completamente (nunca copie frases), em portugues do Brasil, esta
novidade (fonte: {nome_fonte}):
Titulo original: {titulo_original}
Resumo original: {resumo}

REGRAS IMPORTANTES:
- Se a informacao original for curta, EXPANDA com contexto real e relevante: historico
  da franquia/artista/estudio, curiosidades de bastidores amplamente conhecidas,
  recepcao do publico, comparacoes com trabalhos anteriores. NAO invente fatos
  especificos (datas, numeros, declaracoes) que voce nao tenha certeza - contextualize
  com conhecimento geral real, nunca com invencoes especificas.
- NAO seja repetitivo em nenhuma hipotese: cada paragrafo tem que trazer informacao
  nova, sem reafirmar o que ja foi dito com outras palavras.
- Tamanho: entre 600 e 1200 palavras (pode passar de 1200 se o assunto pedir).

REGRAS DE FORMATO (HTML puro, sem Markdown):
1. Paragrafo de abertura envolvente.
2. NO MINIMO 3 subtitulos <h2> (ex: contexto, detalhes, repercussao/expectativa dos fas).
3. Insira 3 notas do autor engracada e leve dentro de <blockquote>, comentando com humor
   de fa (nunca debochado ou ofensivo) espalhados pelo post.
4. Sempre incluir fontes para passar credibilidade.
"""
    return pedir_ia_groq(prompt, temperatura=0.75)


def gerar_cta():
    return """
<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
    <p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Curtiu essa novidade?</p>
    <p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Deixe seu comentario, curta e compartilhe com a galera que também acompanha o assunto!</p>
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
    print("Buscando novidade de cultura pop...")
    titulo_original, resumo, link, fonte = pegar_novidade()

    if titulo_original:
        print(f"Encontrado em [{fonte}]: {titulo_original[:100]}...")
        try:
            categoria = identificar_categoria(titulo_original)
            tags = CATEGORIAS_TAGS.get(categoria, ["cultura pop"])

            palavra_chave = extrair_palavra_chave(titulo_original)
            img_url = buscar_imagem_openverse(palavra_chave)

            novo_titulo = gerar_titulo(titulo_original)
            img_html = gerar_tabela_imagem_blogger(img_url, novo_titulo)
            corpo = gerar_artigo(titulo_original, resumo, fonte)
            cta = gerar_cta()

            rodape = (
                '<hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;" />'
                '<p style="color: #555555; font-size: 13px; font-style: italic; margin-top: 15px;">'
                f'Fonte da noticia original: <a href="{link}" rel="noopener noreferrer" target="_blank">{fonte}</a>'
                '</p>'
            )

            html_final = f"{img_html}{corpo}{cta}{rodape}"
            publicar_no_blogger(novo_titulo, html_final, tags)
            marcar_como_postada(link)
            print("Concluido!")
        except Exception as e:
            print(f"Erro durante geracao/publicacao: {e}")
    else:
        print("Nenhuma novidade nova encontrada em nenhuma fonte.")
