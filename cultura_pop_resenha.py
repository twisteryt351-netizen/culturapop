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

# --- CATEGORIAS DE RESENHA/DOCUMENTARIO (rodizio amplo, tema infinito) ---
EXEMPLO DE TEMAS = [
    "escolha um anime classico que passou na TV aberta brasileira nos anos 60 ah 2026... e faca uma resenha/documentario sobre ele",
    "escolha um anime que quase nunca passou no Brasil ou passou pouco, mas se tornou cult, e conte a historia dele",
    "escolha um anime ou franquia que esta passando atualmente ou vai estrear em breve e faca uma analise aprofundada",
    "faca um documentario sobre a origem e evolucao do mangá no Japao, desde suas raizes ate o mercado atual",
    "faca um documentario sobre a origem e evolucao do anime no Japao, desde os primeiros trabalhos ate os dias atuais",
    "escolha um cartoon classico que marcou geracoes no Brasil (Cartoon Network, Nickelodeon ou similar) e faca uma resenha nostalgica",
    "escolha uma serie de TV americana ou britanica classica que fez sucesso no Brasil e conte sua trajetoria",
    "escolha um quadrinho ou heroi de banca classico (nacional ou internacional) e conte sua historia editorial",
    "faca um documentario sobre a origem do rock and roll e sua evolucao ate o rock classico",
    "faca um documentario sobre a origem e evolucao do heavy metal e seus subgeneros ate hoje",
    "faca um documentario sobre a origem do k-pop e sua explosao global nas ultimas decadas",
    "faca um documentario sobre a origem do j-pop e sua influencia na cultura pop japonesa",
    "escolha uma banda ou artista de rock/pop lendario e conte a historia da carreira dele(a)",
    "escolha um filme classico de ficcao cientifica ou fantasia e faca uma resenha aprofundada sobre seu legado",
    "escolha um game classico dos anos 60/70/80/90/2000/2010/2020/2025/2026... e conte a historia do seu desenvolvimento e impacto cultural",
    "escolha uma franquia de games atual e faca uma analise do que a tornou um fenomeno",

]

ARQUIVO_HISTORICO = "historico_pop_resenha.txt"


def tema_ja_usado(tema):
    if not os.path.exists(ARQUIVO_HISTORICO):
        return False
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        linhas = f.read().splitlines()
    return tema in linhas[-8:]


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
    """ETAPA 1: pede um roteiro/esqueleto detalhado antes de escrever o texto final.
    Isso forca a IA a planejar profundidade em vez de escrever de qualquer jeito."""
    prompt = f"""
Voce e um roteirista de documentarios sobre cultura pop (animes, mangas, cartoons, series,
quadrinhos, musica e games).

Tarefa: {instrucao_tema}

Primeiro, ANTES de escrever o artigo, monte um ESQUELETO detalhado do que sera abordado:
- Escolha e diga EXATAMENTE qual e o titulo/artista/franquia/tema especifico que voce vai
  abordar (seja concreto, nao generico).
- Liste de 5 a 7 topicos/secoes que o artigo vai cobrir (ex: Hook, origem, contexto historico,
  principais nomes envolvidos, curiosidades de bastidores, impacto cultural, legado atual,
  recepcao do publico brasileiro se for o caso, chamada para ação).
- Para cada topico, escreva 1-2 frases resumindo o que sera dito ali, SEM repetir a mesma
  informacao em topicos diferentes.

Responda apenas com esse esqueleto, em texto simples (nao HTML ainda).
"""
    return pedir_ia_groq(prompt, temperatura=0.6)


def gerar_artigo_completo(esqueleto):
    """ETAPA 2: pede o artigo completo usando o esqueleto como guia obrigatorio."""
    prompt = f"""
Voce e um redator de cultura pop premiado, cronista! Escreve artigos estilo documentario/resenha
para um blog de fas muito engajado. Escreva com MUITO capricho, sem pressa - este e um
artigo de destaque do blog. 
Reforçando: Voce e um redator(pesquisa varias fontes) especializado em cultura pop (animes, mangas, quadrinhos, cartoons,
filmes, series, games e musica - rock, pop, k-pop, j-pop, metal) para um blog de fas muito
engajado. Sabe todas as novidades, sabe traçar raciocinio memoria e transcrever de forma agradavel,engraçada, futuca bastidores, sabe uma ou outra fofoquinha, sabe contruir comunidade, Escreva com qualidade alta, sem pressa - capriche de verdade.
Não esquece de citar fontes que serviu de inspiração para o artigo, pode colocar link das fontes para garantir credibilidade do artigo e autoridade. 

Use este esqueleto como guia OBRIGATORIO, desenvolvendo cada topico dele em profundidade,
sem pular nenhum e sem repetir informacao entre secoes:

{esqueleto}

REGRAS DE CONTEUDO:
- Baseie-se em fatos historicos e culturais reais e amplamente conhecidos sobre o tema.
  NAO invente datas, numeros ou citacoes especificas que voce nao tenha certeza - nesses
  casos, descreva de forma mais geral em vez de inventar um fato falso especifico.
- Escreva de forma agradavel e nostalgica, pegando pelo sentimento de quem acompanhou ou
  vai gostar de conhecer o tema.
- PROIBIDO repetir a mesma frase, ideia ou informacao mais de uma vez em palavras diferentes.
  Cada paragrafo tem que avancar a narrativa com informacao nova.
- Tamanho OBRIGATORIO: no MINIMO 1400 palavras. Desenvolva bem cada secao do esqueleto -
  isso naturalmente atinge o tamanho pedido se voce seguir o esqueleto com profundidade real.

REGRAS DE FORMATO (HTML puro, sem Markdown):
1. Um titulo interno como <h1> nao e necessario (o titulo do post e separado), comece
   direto com um paragrafo de abertura instigante.
2. Cada topico do esqueleto vira um subtitulo <h2> proprio.
3. Inclua PELO MENOS 2 notas do autor engracadas e leves, cada uma dentro de <blockquote>,
   com comentarios pessoais de fa (nunca ofensivos), espalhadas em pontos diferentes do texto.
4. Nao inclua links no corpo do texto.
5. Termine com um paragrafo de fechamento reflexivo sobre o legado/importancia do tema.
"""
    return pedir_ia_groq(prompt, temperatura=0.75)


def gerar_titulo(esqueleto):
    prompt = (
        f"Baseado neste esqueleto de artigo:\n{esqueleto}\n\n"
        f"Crie um titulo de blog envolvente, nostalgico, otimizado para SEO, em portugues "
        f"do Brasil, sem aspas. Responda apenas o titulo, texto puro."
    )
    return pedir_ia_groq(prompt, temperatura=0.7).replace('"', '').strip()


def extrair_palavra_chave(esqueleto):
    prompt = (
        f"Baseado neste esqueleto de artigo:\n{esqueleto}\n\n"
        f"De apenas UMA palavra-chave em ingles que descreva visualmente o tema principal "
        f"(ex: 'anime', 'rock concert', 'retro cartoon', 'vintage video game'). "
        f"Responda so a palavra."
    )
    return pedir_ia_groq(prompt, temperatura=0.3).strip().lower().split()[0]


def gerar_cta():
    return """
<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
    <p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Gostou dessa viagem no tempo?</p>
    <p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Curta, deixe seu comentario contando suas lembrancas do assunto e compartilhe com quem tambem vai se emocionar!</p>
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
    print("Esqueleto gerado, escrevendo artigo completo...")

    corpo = gerar_artigo_completo(esqueleto)
    titulo = gerar_titulo(esqueleto)
    palavra_chave = extrair_palavra_chave(esqueleto)
    img_url = buscar_imagem_openverse(palavra_chave)
    img_html = gerar_tabela_imagem_blogger(img_url, titulo)
    cta = gerar_cta()

    aviso = (
        '<p style="font-size: 12px; color: #888; font-style: italic;">Artigo de carater '
        'cultural, historico e opinativo, com fins de entretenimento e nostalgia.</p>'
    )

    html_final = f"{img_html}{corpo}{cta}{aviso}"
    publicar_no_blogger(titulo, html_final, ["resenha", "documentario", "cultura pop"])
    marcar_tema_usado(instrucao_tema)
    print("Concluido!")
