"""Robô de comentários: quem comenta uma palavra-chave (KIT, CAIXA...) recebe resposta pública + o link no direct.
Uso:
  python comentarios.py             verifica os comentários uma vez (o Agendador roda a cada 2 min)
  python comentarios.py --dry-run   mostra o que responderia, sem responder
  python comentarios.py --loop      fica rodando (a cada 2 min)
Textos e links em respostas.json. Já respondidos ficam em respondidos.json (não repete).
Permissões do token: instagram_business_manage_comments e instagram_business_manage_messages.
"""
import os, sys, json, time, random, unicodedata, re, hashlib, datetime as dt
import requests
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
IG_USER = os.getenv("IG_USER_ID", ""); IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
GRAPH = "https://graph.instagram.com/v25.0"
ESTADO = os.path.join(BASE, "respondidos.json")
LOG = os.path.join(BASE, "comentarios.log")
JANELA = dt.timedelta(days=7)  # a Meta só deixa mandar direct para comentário de até 7 dias


def log(msg):
    linha = f"[{dt.datetime.now():%d/%m %H:%M}] {msg}"
    print(linha, flush=True)
    if not os.getenv("GITHUB_ACTIONS"):  # na nuvem o log fica só na tela do Actions (repo é público)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(linha + "\n")


def api(metodo, caminho, **kw):
    r = requests.request(metodo, f"{GRAPH}/{caminho}", params={"access_token": IG_TOKEN, **kw.pop("params", {})}, timeout=60, **kw)
    if not r.ok:
        raise RuntimeError(f"{r.status_code} {r.text[:300]}")
    return r.json()


def normalizar(t):
    t = unicodedata.normalize("NFD", t.upper())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def palavra_do_comentario(texto, palavras):
    t = normalizar(texto)
    for p in palavras:
        if re.search(rf"\b{p}\b", t):
            return p
    return None


def rodar(dry):
    cfg = json.load(open(os.path.join(BASE, "respostas.json"), encoding="utf-8"))
    estado = json.load(open(ESTADO, encoding="utf-8")) if os.path.exists(ESTADO) else {}
    for k in ("comentarios", "enviados", "contagem"):
        estado.setdefault(k, {})
    if "eu" not in estado:  # guarda o próprio usuário para não gastar chamada toda rodada
        estado["eu"] = api("GET", "me", params={"fields": "username"})["username"]
    eu = estado["eu"]
    agora = dt.datetime.now(dt.timezone.utc)
    # limite da Meta: 200 chamadas/hora. Uma chamada traz a contagem de todos os posts;
    # só abre os comentários do post cuja contagem mudou.
    medias = api("GET", f"{IG_USER}/media", params={"fields": "id,comments_count", "limit": 30}).get("data", [])
    novos = 0
    for m in medias:
        total = m.get("comments_count", 0)
        if total == estado["contagem"].get(m["id"], 0):
            continue
        comentarios = api("GET", f"{m['id']}/comments", params={"fields": "id,text,from,timestamp", "limit": 50}).get("data", [])
        for c in comentarios:
            autor = c.get("from") or {}
            quem = autor.get("username") or autor.get("id", "?")
            if c["id"] in estado["comentarios"] or autor.get("username") == eu:
                continue
            quando = dt.datetime.fromisoformat(c["timestamp"].replace("+0000", "+00:00"))
            p = palavra_do_comentario(c.get("text", ""), cfg["palavras"])
            if not p or agora - quando > JANELA:
                continue
            # id do usuário embaralhado: o respondidos.json fica no GitHub público sem dado pessoal
            chave = hashlib.sha256(f"{IG_USER}:{autor.get('id') or c['id']}".encode()).hexdigest()[:20] + f":{p}"
            if dry:
                log(f"[teste] responderia @{quem} ({p}): {c.get('text', '')[:60]}")
                continue
            try:
                api("POST", f"{c['id']}/replies", params={"message": random.choice(cfg["publicas"])})
                ultimo = estado["enviados"].get(chave)
                # a mesma pessoa só recebe o mesmo link de novo depois de 12 h (se comentou outra vez, talvez não achou)
                if not ultimo or agora - dt.datetime.fromisoformat(ultimo) > dt.timedelta(hours=12):
                    api("POST", f"{IG_USER}/messages", json={"recipient": {"comment_id": c["id"]}, "message": {"text": cfg["palavras"][p]}})
                    estado["enviados"][chave] = agora.isoformat()
                estado["comentarios"][c["id"]] = p
                novos += 1
                log(f"respondido @{quem} ({p})")
            except RuntimeError as e:
                log(f"ERRO @{quem} ({p}): {e}")
            json.dump(estado, open(ESTADO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            time.sleep(2)
        if not dry:
            estado["contagem"][m["id"]] = total
            json.dump(estado, open(ESTADO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if novos:
        log(f"{novos} comentário(s) respondido(s)")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    if not IG_TOKEN or not IG_USER:
        sys.exit("Preencha IG_USER_ID e IG_ACCESS_TOKEN no .env")
    while True:
        try:
            rodar(dry)
        except Exception as e:
            log(f"ERRO geral: {e}")
        if "--loop" not in sys.argv:
            break
        time.sleep(120)
