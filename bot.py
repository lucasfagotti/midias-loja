"""Bot de publicação: lê calendario.csv e publica no Instagram (API oficial) e no TikTok (rascunho via API oficial).

Uso:
  python bot.py --dry-run     mostra o que seria publicado agora, sem publicar
  python bot.py               publica o que já passou do horário e ainda não foi publicado
  python bot.py --loop        fica rodando e confere a cada 5 minutos
Configuração: copie .env.exemplo para .env e preencha.
"""
import csv, os, sys, time, json, argparse, hashlib, datetime as dt
import requests
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
IG_USER = os.getenv("IG_USER_ID", "")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
TT_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
PUBLIC_BASE = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")  # ex.: https://raw.githubusercontent.com/usuario/repo/main
GRAPH = "https://graph.instagram.com/v25.0"
CAL = os.path.join(BASE, "calendario.csv")
LOG = os.path.join(BASE, "publicados.json")


def log(msg):
    print(f"[{dt.datetime.now():%d/%m %H:%M}] {msg}", flush=True)


def carregar_publicados():
    return json.load(open(LOG, encoding="utf-8")) if os.path.exists(LOG) else {}


def salvar_publicados(d):
    json.dump(d, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def url_publica(arquivo):
    return f"{PUBLIC_BASE}/{arquivo.replace(os.sep, '/')}"


def esperar_container(cid, tentativas=40):
    for _ in range(tentativas):
        r = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code", "access_token": IG_TOKEN}, timeout=30).json()
        if r.get("status_code") == "FINISHED":
            return
        if r.get("status_code") == "ERROR":
            raise RuntimeError(f"container com erro: {r}")
        time.sleep(15)
    raise TimeoutError("container não ficou pronto")


def ig_criar(params):
    params["access_token"] = IG_TOKEN
    r = requests.post(f"{GRAPH}/{IG_USER}/media", data=params, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"erro ao criar mídia: {r}")
    return r["id"]


def publicar_instagram(tipo, arquivos, legenda):
    if tipo == "imagem":
        cid = ig_criar({"image_url": url_publica(arquivos[0]), "caption": legenda})
    elif tipo == "carrossel":
        filhos = [ig_criar({"image_url": url_publica(a), "is_carousel_item": "true"}) for a in arquivos]
        cid = ig_criar({"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": legenda})
    elif tipo == "reels":
        cid = ig_criar({"media_type": "REELS", "video_url": url_publica(arquivos[0]), "caption": legenda, "share_to_feed": "true"})
        esperar_container(cid)
    else:
        raise ValueError(f"tipo desconhecido: {tipo}")
    r = requests.post(f"{GRAPH}/{IG_USER}/media_publish", data={"creation_id": cid, "access_token": IG_TOKEN}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"erro ao publicar: {r}")
    return r["id"]


def enviar_tiktok_rascunho(arquivo):
    """Envia o vídeo para a caixa de rascunhos do TikTok; você abre o app e toca em Publicar."""
    caminho = os.path.join(BASE, arquivo)
    tamanho = os.path.getsize(caminho)
    init = requests.post("https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                         headers={"Authorization": f"Bearer {TT_TOKEN}", "Content-Type": "application/json; charset=UTF-8"},
                         json={"source_info": {"source": "FILE_UPLOAD", "video_size": tamanho, "chunk_size": tamanho, "total_chunk_count": 1}},
                         timeout=60).json()
    if init.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"erro TikTok: {init}")
    up = init["data"]["upload_url"]
    with open(caminho, "rb") as f:
        requests.put(up, data=f, headers={"Content-Range": f"bytes 0-{tamanho - 1}/{tamanho}", "Content-Type": "video/mp4"}, timeout=300).raise_for_status()
    return init["data"]["publish_id"]


def rodar(dry):
    feitos = carregar_publicados()
    agora = dt.datetime.now()
    for linha in csv.DictReader(open(CAL, encoding="utf-8")):
        chave = f"{linha['data']} {linha['hora']} {linha['plataforma']} {linha['arquivos']}"
        quando = dt.datetime.strptime(f"{linha['data']} {linha['hora']}", "%Y-%m-%d %H:%M")
        # horário com variação de 0 a 25 min (fixa por post) para não postar sempre no minuto exato
        quando += dt.timedelta(minutes=int(hashlib.md5(chave.encode()).hexdigest(), 16) % 26)
        if quando > agora or (chave in feitos and "id" in feitos[chave]) or feitos.get(chave, {}).get("falhas", 0) >= 3:
            continue
        if linha["plataforma"] == "tiktok" and not TT_TOKEN:
            continue  # sem token do TikTok: posta manual pelo TikTok Studio
        arquivos = [a.strip() for a in linha["arquivos"].split("|")]
        if dry:
            log(f"[simulação] {linha['plataforma']} {linha['tipo']}: {arquivos} | {linha['legenda'][:60]}...")
            continue
        try:
            if linha["plataforma"] == "instagram":
                pid = publicar_instagram(linha["tipo"], arquivos, linha["legenda"])
            elif linha["plataforma"] == "tiktok":
                pid = enviar_tiktok_rascunho(arquivos[0])
            else:
                continue
            feitos[chave] = {"id": pid, "em": f"{agora:%Y-%m-%d %H:%M}"}
            salvar_publicados(feitos)
            log(f"OK {linha['plataforma']} {linha['tipo']} -> {pid}")
        except Exception as e:
            falhas = feitos.get(chave, {}).get("falhas", 0) + 1
            feitos[chave] = {"falhas": falhas, "erro": str(e)[:300]}
            salvar_publicados(feitos)
            log(f"ERRO ({falhas}/3) {linha['plataforma']} {arquivos}: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--loop", action="store_true")
    a = ap.parse_args()
    if not a.dry_run and (not IG_TOKEN or not PUBLIC_BASE):
        sys.exit("Preencha o arquivo .env antes (veja .env.exemplo).")
    while True:
        rodar(a.dry_run)
        if not a.loop:
            break
        time.sleep(300)
