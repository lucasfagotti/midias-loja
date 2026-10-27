"""Robô de anúncios (Meta Marketing API). Plano em ads.json; ids criados em ads_estado.json.
Uso:
  python ads.py criar [id]   cria campanhas/conjuntos/anúncios do ads.json, TUDO PAUSADO
  python ads.py ativar kit   liga a campanha (só com o OK do Lucas: isso gasta dinheiro)
  python ads.py pausar kit   pausa a campanha
  python ads.py monitorar    aplica as regras de corte (roda na nuvem 3x por dia)
  python ads.py resumo       mostra gasto, cliques, checkouts e vendas (só no PC: números não vão para o log público)
Trava principal: o limite de gastos da conta, definido pelo Lucas na Meta. Este robô nunca aumenta orçamento.
Token: variável META_ADS_TOKEN (usuário do sistema robo-ads).
"""
import os, sys, json, time, datetime as dt
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
G = "https://graph.facebook.com/v25.0"
TOKEN = os.getenv("META_ADS_TOKEN", "")
PLANO = json.load(open(os.path.join(BASE, "ads.json"), encoding="utf-8"))
ESTADO = os.path.join(BASE, "ads_estado.json")
PLANOS = {c["id"]: c for c in PLANO["campanhas"]}
NUVEM = bool(os.getenv("GITHUB_ACTIONS"))


def api(metodo, caminho, **dados):
    # listas e objetos vão como JSON (formato que a Graph API espera em campos como targeting)
    dados = {k: json.dumps(v) if isinstance(v, (dict, list, bool)) else v for k, v in dados.items()}
    dados["access_token"] = TOKEN
    if metodo == "GET":
        r = requests.get(f"{G}/{caminho}", params=dados, timeout=120)
    else:
        r = requests.post(f"{G}/{caminho}", data=dados, timeout=120)
    j = r.json()
    if "error" in j:
        e = j["error"]
        raise RuntimeError(f"{e.get('message')} | {e.get('error_user_title', '')} {e.get('error_user_msg', '')}".strip())
    return j


def ler_estado():
    return json.load(open(ESTADO, encoding="utf-8")) if os.path.exists(ESTADO) else {"campanhas": {}, "pausados_pelo_robo": {}}


def gravar_estado(e):
    json.dump(e, open(ESTADO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def esperar_video(vid, limite=60):
    for _ in range(limite):
        st = api("GET", vid, fields="status").get("status", {}).get("video_status")
        if st == "ready":
            return
        if st == "error":
            raise RuntimeError(f"vídeo {vid} deu erro no processamento")
        time.sleep(10)
    raise RuntimeError(f"vídeo {vid} não ficou pronto")


def criar(so=None):
    e = ler_estado(); conta, pub = PLANO["conta"], PLANO["publico"]
    for c in PLANO["campanhas"]:
        if so and c["id"] != so:
            continue
        ec = e["campanhas"].setdefault(c["id"], {"anuncios": {}})
        if "campanha" not in ec:
            ec["campanha"] = api("POST", f"{conta}/campaigns", name=c["nome"], objective="OUTCOME_SALES" if c.get("tipo", "vendas") == "vendas" else "OUTCOME_TRAFFIC", status="PAUSED",
                                 special_ad_categories=[], buying_type="AUCTION", is_adset_budget_sharing_enabled=False)["id"]
            gravar_estado(e); print("campanha", c["nome"])
        if "conjunto" not in ec:
            alvo = {"geo_locations": {"countries": [pub["pais"]]}, "age_min": pub["idade_min"], "age_max": pub["idade_max"],
                    "targeting_automation": {"advantage_audience": 1}}
            if c.get("tipo", "vendas") == "vendas":
                extra = {"optimization_goal": "OFFSITE_CONVERSIONS",
                         "promoted_object": {"pixel_id": PLANO["pixel"], "custom_event_type": "PURCHASE"}}
            else:
                alvo["publisher_platforms"] = ["instagram"]
                extra = {"optimization_goal": "VISIT_INSTAGRAM_PROFILE", "destination_type": "INSTAGRAM_PROFILE"}
            ec["conjunto"] = api("POST", f"{conta}/adsets", name=f"{c['nome']} - Brasil", campaign_id=ec["campanha"], status="PAUSED",
                                 daily_budget=int(c["orcamento_dia"] * 100), billing_event="IMPRESSIONS",
                                 bid_strategy="LOWEST_COST_WITHOUT_CAP", targeting=alvo, **extra)["id"]
            gravar_estado(e); print("conjunto", c["nome"])
        for a in c["anuncios"]:
            if a["nome"] in ec["anuncios"]:
                continue
            vid = api("POST", f"{conta}/advideos", file_url=f"{PLANO['base_midia']}/{a['video']}", name=a["nome"])["id"]
            esperar_video(vid)
            cri = api("POST", f"{conta}/adcreatives", name=a["nome"], object_story_spec={
                "page_id": PLANO["pagina"], "instagram_user_id": PLANO["instagram"],
                "video_data": {"video_id": vid, "image_url": f"{PLANO['base_midia']}/{a['capa']}", "message": a["texto"], "title": a["titulo"],
                               "call_to_action": {"type": "LEARN_MORE" if c.get("tipo", "vendas") == "vendas" else "VISIT_INSTAGRAM_PROFILE",
                                                  "value": {"link": c["link"]}}}})["id"]
            ec["anuncios"][a["nome"]] = api("POST", f"{conta}/ads", name=a["nome"], adset_id=ec["conjunto"],
                                            creative={"creative_id": cri}, status="PAUSED")["id"]
            gravar_estado(e); print("anúncio", a["nome"])
        # conjunto e anúncios ficam ACTIVE por dentro; quem liga/desliga o gasto é a campanha
        api("POST", ec["conjunto"], status="ACTIVE")
        for ad in ec["anuncios"].values():
            api("POST", ad, status="ACTIVE")
    print("Tudo criado e PAUSADO na campanha. Nada gasta até rodar: python ads.py ativar <id>")


def mudar(cid, status):
    e = ler_estado()
    api("POST", e["campanhas"][cid]["campanha"], status=status)
    print(f"campanha {cid}: {status}")


def numeros(obj, periodo="maximum"):
    d = api("GET", f"{obj}/insights", fields="spend,inline_link_clicks,actions", date_preset=periodo).get("data", [])
    if not d:
        return {"gasto": 0.0, "cliques": 0, "checkouts": 0, "vendas": 0}
    d = d[0]; acoes = {a["action_type"]: int(float(a["value"])) for a in d.get("actions", [])}
    return {"gasto": float(d.get("spend", 0)), "cliques": int(d.get("inline_link_clicks", 0)),
            "checkouts": max(acoes.get("offsite_conversion.fb_pixel_initiate_checkout", 0), acoes.get("initiate_checkout", 0)),
            "vendas": max(acoes.get("offsite_conversion.fb_pixel_purchase", 0), acoes.get("purchase", 0))}


def monitorar():
    e = ler_estado(); r = PLANO["regras"]; mudou = False
    mes = numeros(PLANO["conta"], "this_month")["gasto"]
    for cid, ec in e["campanhas"].items():
        camp = api("GET", ec["campanha"], fields="status")["status"]
        if camp != "ACTIVE":
            continue
        if mes >= r["limite_mes"]:  # segunda trava, além do limite da conta na Meta
            api("POST", ec["campanha"], status="PAUSED"); print(f"{cid}: limite do mês atingido, campanha pausada"); continue
        ativos = 0
        for nome, ad in ec["anuncios"].items():
            if api("GET", ad, fields="status")["status"] != "ACTIVE":
                continue
            n = numeros(ad)
            if PLANOS[cid].get("tipo", "vendas") == "seguidores":
                custo = n["gasto"] / n["cliques"] if n["cliques"] else 99
                motivo = "visita ao perfil cara demais" if n["gasto"] >= r["seguidores_corte_gasto"] and custo > r["seguidores_custo_max_visita"] else None
            else:
                motivo = ("gastou o corte sem nenhum checkout" if n["gasto"] >= r["corte_sem_checkout"] and n["checkouts"] == 0 else
                          "gastou o corte sem nenhuma venda" if n["gasto"] >= r["corte_sem_venda"] and n["vendas"] == 0 else None)
            if motivo:
                api("POST", ad, status="PAUSED")
                e["pausados_pelo_robo"][ad] = {"nome": nome, "motivo": motivo, "em": f"{dt.datetime.now():%Y-%m-%d %H:%M}"}
                mudou = True; print(f"pausado: {nome} ({motivo})")
            else:
                ativos += 1
        if ativos == 0:
            api("POST", ec["campanha"], status="PAUSED"); mudou = True
            print(f"{cid}: todos os anúncios cortados, campanha pausada")
            if NUVEM:
                os.system(f'gh issue create --repo "$GITHUB_REPOSITORY" --title "📣 Anúncios da campanha {cid} pausados" '
                          f'--body "As regras de corte pausaram todos os anúncios. Peça ao Claude para analisar e criar novos criativos."')
    if mudou:
        gravar_estado(e)
    print("monitoramento ok")


def resumo():
    e = ler_estado()
    print(f"Mês: R$ {numeros(PLANO['conta'], 'this_month')['gasto']:.2f} de R$ {PLANO['regras']['limite_mes']}")
    for cid, ec in e["campanhas"].items():
        print(f"\n[{cid}] campanha {api('GET', ec['campanha'], fields='status')['status']}")
        for nome, ad in ec["anuncios"].items():
            n = numeros(ad); st = api("GET", ad, fields="status")["status"]
            print(f"  {st:<7} {nome:<28} R$ {n['gasto']:>6.2f} | {n['cliques']} cliques | {n['checkouts']} checkouts | {n['vendas']} vendas")


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("Falta META_ADS_TOKEN")
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "criar":
        criar(sys.argv[2] if len(sys.argv) > 2 else None)
    elif acao in ("ativar", "pausar") and len(sys.argv) > 2:
        mudar(sys.argv[2], "ACTIVE" if acao == "ativar" else "PAUSED")
    elif acao == "monitorar":
        monitorar()
    elif acao == "resumo" and not NUVEM:
        resumo()
    else:
        sys.exit(__doc__)
