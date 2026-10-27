"""Números do perfil para o widget: seguidores, seguindo, posts e alcance do dia.
Roda junto com os robôs, mas só consulta a API 1 vez por hora. Saída: estatisticas.json
(seguidores do fim de cada dia ficam em "dias", para o widget calcular quanto ganhou).
"""
import os, json, datetime as dt
import requests
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
IG_USER = os.getenv("IG_USER_ID", "")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
GRAPH = "https://graph.instagram.com/v25.0"
ARQ = os.path.join(BASE, "estatisticas.json")


def main():
    est = json.load(open(ARQ, encoding="utf-8")) if os.path.exists(ARQ) else {"dias": {}}
    agora = dt.datetime.now()
    ultimo = est.get("atualizado")
    if ultimo and agora - dt.datetime.fromisoformat(ultimo) < dt.timedelta(minutes=55):
        return
    perfil = requests.get(f"{GRAPH}/{IG_USER}", params={"fields": "followers_count,follows_count,media_count",
                                                         "access_token": IG_TOKEN}, timeout=30).json()
    if "followers_count" not in perfil:
        print("erro ao ler o perfil:", str(perfil)[:200]); return
    est.update(atualizado=agora.isoformat(timespec="minutes"), seguidores=perfil["followers_count"],
               seguindo=perfil.get("follows_count", 0), posts=perfil.get("media_count", 0))
    est["dias"][agora.date().isoformat()] = perfil["followers_count"]
    est["dias"] = dict(sorted(est["dias"].items())[-60:])
    try:  # alcance e visitas ao perfil de hoje (pode não vir em conta muito nova)
        ins = requests.get(f"{GRAPH}/{IG_USER}/insights", params={"metric": "reach,profile_views", "period": "day",
                                                                   "metric_type": "total_value", "access_token": IG_TOKEN}, timeout=30).json()
        for m in ins.get("data", []):
            est[{"reach": "alcance_hoje", "profile_views": "visitas_hoje"}[m["name"]]] = m.get("total_value", {}).get("value", 0)
    except Exception as e:
        print("insights indisponíveis:", e)
    json.dump(est, open(ARQ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"seguidores: {est['seguidores']}")


if __name__ == "__main__":
    main()
