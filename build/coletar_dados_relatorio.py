#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera build/relatorios_dados.json: SÓ NÚMEROS (nenhuma interpretação/texto),
agregados por período/campanha/conjunto/anúncio a partir dos mesmos dados que
alimentam o dashboard (mídia paga x Leads). É o insumo lido pela Routine do
Claude (ver GUIA-RELATORIOS.md) para escrever build/relatorios.json — garante
que os números do texto batem 1:1 com o site sem depender do Claude "fazer
conta". Não chama nenhuma API de IA/LLM.

Uso:
    python build/coletar_dados_relatorio.py --out build/relatorios_dados.json
    python build/coletar_dados_relatorio.py --leads-file leads.csv --meta-file meta.csv --out build/relatorios_dados.json

Sem --leads-file/--meta-file, busca os CSVs públicos da planilha (mesma URL de
build.py) — precisa de acesso a docs.google.com (o runner do GitHub Actions tem;
o sandbox do agente normalmente não).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as bp  # reaproveita fetch/parse/process/constantes de build.py
from relatorio_lib import BRT, d, build_periods, in_range, agg, derived, shift_back


def daily_series(meta: list[dict], leads: list[dict], start, end, camp=None, adset=None, ad=None) -> list[dict]:
    """Uma linha por dia (spend/leads/mqls + derivadas) — dá ao Claude a base
    pra enxergar tendência (ex.: CPM subindo/Tx-MQL caindo N dias seguidos)."""
    out = []
    cur = start
    while cur <= end:
        a = derived(agg(meta, leads, cur, cur, camp=camp, adset=adset, ad=ad))
        if a["spend"] or a["leads"]:
            out.append({
                "d": cur.strftime("%Y-%m-%d"),
                "spend": round(a["spend"], 2), "impr": a["impr"], "clicks": a["clicks"],
                "leads": a["leads"], "mqls": a["mqls"],
                "cpm": _r(a["cpm"]), "ctr": _r(a["ctr"], 4), "cpl": _r(a["cpl"]),
                "txmql": _r(a["txmql"], 4), "cpmql": _r(a["cpmql"]),
            })
        cur += timedelta(days=1)
    return out


def _r(v, nd=2):
    return None if v is None else round(v, nd)


def totais_dict(a: dict) -> dict:
    return {
        "spend": round(a["spend"], 2), "impr": a["impr"], "clicks": a["clicks"],
        "leads": a["leads"], "mqls": a["mqls"],
        "cpm": _r(a["cpm"]), "ctr": _r(a["ctr"], 4), "cpl": _r(a["cpl"]),
        "convform": _r(a["convform"], 4), "txmql": _r(a["txmql"], 4), "cpmql": _r(a["cpmql"]),
    }


def breakdown(meta: list[dict], leads: list[dict], start, end, dim: str, camp_filter=None) -> list[dict]:
    """Agrega por campanha/conjunto/anúncio dentro do período, com série diária."""
    def key_of(r):
        if dim == "camp":
            return r["camp"]
        if dim == "adset":
            return (r["camp"], r["adset"])
        return (r["camp"], r["adset"], r["ad"])

    keys = set()
    for r in meta:
        if in_range(r["d"], start, end) and (camp_filter is None or r["camp"] == camp_filter):
            keys.add(key_of(r))
    for r in leads:
        if in_range(r["d"], start, end) and (camp_filter is None or r["camp"] == camp_filter):
            keys.add(key_of(r))

    out = []
    for k in sorted(keys, key=lambda x: str(x)):
        if dim == "camp":
            camp, adset, ad = k, None, None
        elif dim == "adset":
            camp, adset, ad = k[0], k[1], None
        else:
            camp, adset, ad = k

        a = derived(agg(meta, leads, start, end, camp=camp, adset=adset, ad=ad))
        if not a["spend"] and not a["leads"]:
            continue
        row = totais_dict(a)
        if dim == "camp":
            row["campanha"] = camp
        elif dim == "adset":
            row["campanha"], row["conjunto"] = camp, adset
        else:
            row["campanha"], row["conjunto"], row["anuncio"] = camp, adset, ad
        row["serie_diaria"] = daily_series(meta, leads, start, end, camp=camp, adset=adset, ad=ad)
        out.append(row)
    out.sort(key=lambda r: -r["spend"])
    return out


def periodo_payload(meta: list[dict], leads: list[dict], today, start, end) -> dict:
    cur = derived(agg(meta, leads, start, end))
    ref7 = derived(agg(meta, leads, today - timedelta(days=6), today))
    ref14 = derived(agg(meta, leads, today - timedelta(days=13), today))
    ref30 = derived(agg(meta, leads, today - timedelta(days=29), today))
    p1s, p1e = shift_back(start, end, 1)
    anterior = derived(agg(meta, leads, p1s, p1e))
    return {
        "range": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "totais": totais_dict(cur),
        "comparativos": {
            "7d": totais_dict(ref7), "14d": totais_dict(ref14), "30d": totais_dict(ref30),
            "periodo_anterior_mesmo_tamanho": {
                "range": {"start": p1s.strftime("%Y-%m-%d"), "end": p1e.strftime("%Y-%m-%d")},
                **totais_dict(anterior),
            },
        },
        "por_campanha": breakdown(meta, leads, start, end, "camp"),
        "por_conjunto": breakdown(meta, leads, start, end, "adset"),
        "por_anuncio": breakdown(meta, leads, start, end, "ad"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file")
    ap.add_argument("--meta-file")
    ap.add_argument("--out", default="build/relatorios_dados.json")
    args = ap.parse_args()

    leads_rows = bp.load_rows(bp.EXPORT_URL.format(sid=bp.SPREADSHEET_ID, gid=bp.GID_LEADS), args.leads_file)
    meta_rows = bp.load_rows(bp.EXPORT_URL.format(sid=bp.SPREADSHEET_ID, gid=bp.GID_META), args.meta_file)
    data = bp.process(leads_rows, meta_rows)
    leads, meta = data["leads"], data["meta"]

    now_brt = datetime.now(BRT)
    today = now_brt.date()
    date_min = d(data["build"]["date_min"]) if data["build"]["date_min"] else None
    date_max = d(data["build"]["date_max"]) if data["build"]["date_max"] else None

    periods = build_periods(today, date_min, date_max)

    out = {
        "generated_at": now_brt.strftime("%d/%m/%Y %H:%M"),
        "generated_at_iso": now_brt.isoformat(),
        "fonte": "Números brutos agregados a partir do funil (mídia paga × Leads) — insumo para a "
                 "Routine do Claude escrever build/relatorios.json (Insights de Tráfego). Sem "
                 "interpretação/texto aqui, só aritmética.",
        "params": {
            "tax_factor": bp.TAX_FACTOR,
            "sample_min_spend": bp.SAMPLE_MIN_SPEND,
            "sample_min_mqls": bp.SAMPLE_MIN_MQLS,
            "meta_cpmql": bp.META_CPMQL,
            "meta_cac": bp.META_CAC,
            "volume_min_amostral": bp.VOLUME_MIN_AMOSTRAL,
            "n_dias_corte": bp.N_DIAS_CORTE,
        },
        "periodos": {},
    }
    for key, (start, end, label) in periods.items():
        out["periodos"][key] = {"label": label, **periodo_payload(meta, leads, today, start, end)}

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("== coletar_dados_relatorio ok ==", file=sys.stderr)
    print(f"  periodos: {list(out['periodos'].keys())}", file=sys.stderr)
    print(f"  out: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
