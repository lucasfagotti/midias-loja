"""Lançamento dos produtos novos: liga as palavras no robô de comentários e agenda os Reels.
Uso: python agendar_lancamento.py links.json AAAA-MM-DD
links.json: {"ESTOQUE": "https://pay.kiwify.com.br/...", "ML": "...", "RESPOSTAS": "...", "REELS": "...",
             "CALENDARIO": "...", "CONTEUDO": "...", "COMBO": "..."}   (pode faltar algum: ele é pulado)
Agenda um Reel a cada 2 dias a partir da data, às 15:00, no Instagram e no TikTok (rascunho/manual).
Depois: git add + commit + push (a nuvem passa a usar).
"""
import os, sys, json, csv, datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.join(os.path.dirname(BASE), "videos", "roteiros", "lancamento")
DM = {
    "ESTOQUE": "Oi! Aqui está a planilha Estoque que Gira 📦\nEla mostra quanto dinheiro está parado na prateleira, a curva ABC, o preço mínimo de promoção e quanto repor de cada produto. Vem com guia ilustrado.\n👉 {link}\nQualquer dúvida, é só responder aqui!",
    "ML": "Oi! Aqui está o Kit Vendedor Mercado Livre 2026 🧮\nCalculadora com as taxas novas, alerta do degrau dos R$ 79, Clássico x Premium e bônus TikTok Shop, mais o guia do anúncio.\n👉 {link}\nQualquer dúvida, me chama aqui.",
    "RESPOSTAS": "Oi! Aqui está o Pack Respostas Prontas 💬\n122 mensagens para chat, WhatsApp, avaliações, trocas e reclamações, em PDF e Word para copiar e colar.\n👉 {link}\nQualquer dúvida, responde aqui!",
    "REELS": "Oi! Aqui está o Reels Narrados para sua Loja 🎬\nVocê manda as fotos dos produtos e recebe 10 vídeos narrados com a sua cor e o seu @, em até 5 dias úteis, sem reunião. Veja exemplos: https://lucasfagotti.github.io/midias-loja/site/exemplos-reels.html\n👉 {link}",
    "CALENDARIO": "Oi! Aqui está o Calendário Comercial 2027 📅\n32 datas para moda e calçados, quando começar a preparar, kits e ofertas que respeitam a margem. Planilha + guia mês a mês.\n👉 {link}\nQualquer dúvida, me chama!",
    "CONTEUDO": "Oi! Aqui está a assinatura Conteúdo do Mês 📲\nTodo mês: 20 posts editáveis no Canva, 8 roteiros de Reels, Stories e legendas prontas. Cancele quando quiser.\n👉 {link}\nQualquer dúvida, responde aqui!",
    "COMBO": "Oi! Aqui está o Combo Lojista Completo 🎁\nKit Vendedor + Auto-Consultoria + Gestão Financeira + Pack 36 Posts, tudo junto por R$ 127.\n👉 {link}\nQualquer dúvida, é só chamar!",
}
ARQ = {"ESTOQUE": "estoque", "ML": "ml", "RESPOSTAS": "respostas", "REELS": "reels", "CALENDARIO": "calendario", "CONTEUDO": "conteudo"}

links = json.load(open(sys.argv[1], encoding="utf-8")); inicio = dt.date.fromisoformat(sys.argv[2])
resp = json.load(open(os.path.join(BASE, "respostas.json"), encoding="utf-8"))
for k, link in links.items():
    if k in DM and link.startswith("https://"):
        resp["palavras"][k] = DM[k].format(link=link); print("robô de comentários:", k)
json.dump(resp, open(os.path.join(BASE, "respostas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

cal = os.path.join(BASE, "calendario.csv"); linhas = []
ordem = [k for k in ARQ if k in links]
for i, k in enumerate(ordem):
    r = json.load(open(os.path.join(ROT, f"{ARQ[k]}.json"), encoding="utf-8"))
    legenda = r.get("legenda") or f"Comente {k} que eu te mando o link."
    dia = (inicio + dt.timedelta(days=2 * i)).isoformat()
    for plat in ("instagram", "tiktok"):
        linhas.append({"data": dia, "hora": "15:00", "plataforma": plat, "tipo": "reels", "arquivos": f"midia/lancamento/{ARQ[k]}_reel.mp4", "legenda": legenda})
with open(cal, "a", newline="", encoding="utf-8") as fh:
    csv.DictWriter(fh, fieldnames=["data", "hora", "plataforma", "tipo", "arquivos", "legenda"]).writerows(linhas)
print(f"{len(linhas)} publicações agendadas a partir de {inicio}")
