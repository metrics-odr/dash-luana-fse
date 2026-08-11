#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera build/relatorios.json (aba "Relatório" -> "Insights de Tráfego") aplicando
DETERMINISTICAMENTE as regras de build/GUIA-RELATORIOS.md sobre os mesmos dados
que alimentam o dashboard (mídia paga x Leads).

Não chama nenhuma API de IA/LLM — é só aritmética + templates de texto em
Python. Custo zero de créditos Anthropic, roda 100% dentro do GitHub Actions.

Uso:
    python build/gerar_relatorios.py --out build/relatorios.json
    python build/gerar_relatorios.py --leads-file leads.csv --meta-file meta.csv --out build/relatorios.json

Sem --leads-file/--meta-file, busca os CSVs públicos da planilha (mesma URL de
build.py) — precisa de acesso a docs.google.com (o runner do GitHub Actions tem;
o sandbox do agente normalmente não).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as bp  # reaproveita fetch/parse/process/constantes de build.py

BRT = bp.BRT

# --------------------------------------------------------------------------- #
# Datas / períodos — espelha PRESETS de build/app.js
# --------------------------------------------------------------------------- #
def d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def ds(x: date) -> str:
    return x.strftime("%Y-%m-%d")


def month_bounds(any_day: date, offset_months: int = 0):
    y, m = any_day.year, any_day.month
    m += offset_months
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    first = date(y, m, 1)
    if m == 12:
        last = date(y, 12, 31)
    else:
        nxt = date(y, m + 1, 1)
        last = nxt - timedelta(days=1)
    return first, last


def build_periods(today: date, date_min: date | None, date_max: date | None):
    dmin = date_min or today
    dmax = date_max or today
    mes_f, _ = month_bounds(today, 0)
    mespass_f, mespass_l = month_bounds(today, -1)
    return {
        "hoje":    (today, today, "Hoje"),
        "ontem":   (today - timedelta(days=1), today - timedelta(days=1), "Ontem"),
        "3d":      (today - timedelta(days=2), today, "3 dias"),
        "7d":      (today - timedelta(days=6), today, "7 dias"),
        "14d":     (today - timedelta(days=13), today, "14 dias"),
        "30d":     (today - timedelta(days=29), today, "30 dias"),
        "mes":     (mes_f, today, "Este mês"),
        "mespass": (mespass_f, mespass_l, "Mês passado"),
        "todo":    (dmin, dmax, "Todo período"),
    }


# --------------------------------------------------------------------------- #
# Agregação
# --------------------------------------------------------------------------- #
def in_range(row_date: str | None, start: date, end: date) -> bool:
    if not row_date:
        return False
    try:
        rd = d(row_date)
    except ValueError:
        return False
    return start <= rd <= end


def agg(meta: list[dict], leads: list[dict], start: date, end: date, camp: str | None = None) -> dict:
    m = [r for r in meta if in_range(r["d"], start, end) and (camp is None or r["camp"] == camp)]
    l = [r for r in leads if in_range(r["d"], start, end) and (camp is None or r["camp"] == camp)]
    spend = sum(r["sp"] for r in m) * bp.TAX_FACTOR
    impr = sum(r["im"] for r in m)
    clicks = sum(r["cl"] for r in m)
    n_leads = len(l)
    n_mqls = sum(r["q"] for r in l)
    return {"spend": spend, "impr": impr, "clicks": clicks, "leads": n_leads, "mqls": n_mqls}


def derived(a: dict) -> dict:
    spend, impr, clicks, leads, mqls = a["spend"], a["impr"], a["clicks"], a["leads"], a["mqls"]
    return {
        "cpm": (spend / impr * 1000) if impr else None,
        "ctr": (clicks / impr) if impr else None,
        "cpl": (spend / leads) if leads else None,
        "convform": (leads / clicks) if clicks else None,
        "txmql": (mqls / leads) if leads else None,
        "cpmql": (spend / mqls) if mqls else None,
        **a,
    }


def shift_back(start: date, end: date, n: int) -> tuple[date, date]:
    """Janela imediatamente anterior, mesmo tamanho, deslocada n vezes."""
    span = (end - start).days + 1
    new_end = start - timedelta(days=1 + span * (n - 1))
    new_start = new_end - timedelta(days=span - 1)
    return new_start, new_end


# --------------------------------------------------------------------------- #
# Formatação
# --------------------------------------------------------------------------- #
def money(v) -> str:
    if v is None:
        return "—"
    return f"R$ {v:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def pct(v) -> str:
    if v is None:
        return "—"
    return f"{v * 100:.1f}%".replace(".", ",")


def num(v) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}".replace(",", ".")


def meta_status(nome: str, valor) -> str:
    return "meta não definida" if valor is None else f"meta {nome} = {money(valor)}"


# --------------------------------------------------------------------------- #
# Blocos de texto (regras do GUIA-RELATORIOS.md)
# --------------------------------------------------------------------------- #
def bloco_resumo(label: str, cur: dict, ref7: dict, ref14: dict, ref30: dict, meta_cpmql, meta_cac) -> str:
    status_metas = (
        f"<b>Status das metas:</b> CPMQL — {meta_status('CPMQL', meta_cpmql)}; "
        f"CAC — {meta_status('CAC', meta_cac)} (dados de venda ainda não conectados)."
    )
    linhas = [
        f"<p>{status_metas}</p>",
        f"<p><b>{label}:</b> gasto {money(cur['spend'])} · leads {num(cur['leads'])} · "
        f"MQLs {num(cur['mqls'])} · Tx‑MQL {pct(cur['txmql'])} · CPL {money(cur['cpl'])} · "
        f"CPMQL {money(cur['cpmql'])}"
        + (f" (dentro da meta)" if meta_cpmql is not None and cur['cpmql'] is not None and cur['cpmql'] <= meta_cpmql
           else f" (acima da meta)" if meta_cpmql is not None and cur['cpmql'] is not None and cur['cpmql'] > meta_cpmql
           else "") + ".</p>",
        "<p><b>Comparação com janelas de referência</b> (terminando na última data com dado):</p>",
        "<ul>"
        f"<li>7 dias: gasto {money(ref7['spend'])} · MQLs {num(ref7['mqls'])} · "
        f"Tx‑MQL {pct(ref7['txmql'])} · CPL {money(ref7['cpl'])} · CPMQL {money(ref7['cpmql'])}</li>"
        f"<li>14 dias: gasto {money(ref14['spend'])} · MQLs {num(ref14['mqls'])} · "
        f"Tx‑MQL {pct(ref14['txmql'])} · CPL {money(ref14['cpl'])} · CPMQL {money(ref14['cpmql'])}</li>"
        f"<li>30 dias: gasto {money(ref30['spend'])} · MQLs {num(ref30['mqls'])} · "
        f"Tx‑MQL {pct(ref30['txmql'])} · CPL {money(ref30['cpl'])} · CPMQL {money(ref30['cpmql'])}</li>"
        "</ul>",
    ]
    return "".join(linhas)


def bloco_leitura_funil(cur: dict, volume_min: int) -> str:
    faltam_mqls = max(0, volume_min - cur["mqls"])
    if cur["leads"] == 0:
        return "<p>Sem leads no período — sem base para leitura de funil.</p>"
    partes = []
    if cur["mqls"] < volume_min:
        cpmql_ref = cur["cpmql"] or 0
        gasto_estimado = cpmql_ref * faltam_mqls if cpmql_ref else None
        partes.append(
            f"<p><b>Ruído por volume baixo:</b> {num(cur['mqls'])} MQL(s) no período, abaixo do "
            f"volume mínimo amostral ({volume_min}). Faltam {faltam_mqls} MQL(s) "
            + (f"(~{money(gasto_estimado)} de gasto no ritmo atual)" if gasto_estimado else "")
            + " para virar amostra confiável — nenhuma conclusão de qualidade deve ser tirada ainda.</p>"
        )
    else:
        partes.append(
            f"<p><b>Funcionando:</b> volume de {num(cur['mqls'])} MQL(s) já é amostra confiável "
            f"(≥ {volume_min}); Tx‑MQL de {pct(cur['txmql'])} e CPMQL de {money(cur['cpmql'])} "
            f"podem ser usados para decisão.</p>"
        )
    partes.append(
        "<p><b>Gargalo de dado:</b> funil só vai até MQL (ver bloco dedicado abaixo) — "
        "Tx‑Agendamento, No‑Show, Tx‑Venda, CAC e ROAS não podem ser lidos ainda.</p>"
    )
    return "".join(partes)


def classify_campaigns(meta: list[dict], leads: list[dict], start: date, end: date,
                        volume_min: int, meta_cpmql, meta_cac, n_dias_corte: int) -> list[tuple]:
    camps = sorted({r["camp"] for r in meta if in_range(r["d"], start, end)} |
                    {r["camp"] for r in leads if in_range(r["d"], start, end)})
    out = []
    for camp in camps:
        w0 = derived(agg(meta, leads, start, end, camp))
        w1s, w1e = shift_back(start, end, 1)
        w2s, w2e = shift_back(start, end, 2)
        w1 = derived(agg(meta, leads, w1s, w1e, camp))
        w2 = derived(agg(meta, leads, w2s, w2e, camp))

        if w0["mqls"] < volume_min:
            faltam = volume_min - w0["mqls"]
            cpmql_ref = w0["cpmql"] or w1["cpmql"]
            gasto_falta = f" (~{money(cpmql_ref * faltam)} de gasto no ritmo atual)" if cpmql_ref else ""
            tag, motivo = "observar", (
                f"volume {w0['mqls']} MQL(s) &lt; mínimo amostral ({volume_min}); "
                f"faltam {faltam} MQL(s){gasto_falta} para amostra suficiente."
            )
        elif meta_cpmql is not None and w0["mqls"] == 0 and w0["cpl"] is not None:
            tag, motivo = "corte", (
                f"volume suficiente, zero conversão qualificada e CPL {money(w0['cpl'])} acima "
                f"do teto por {n_dias_corte}+ dias consecutivos (referência: meta CPMQL {money(meta_cpmql)})."
            )
        elif (w0["txmql"] is not None and w1["txmql"] is not None and w2["txmql"] is not None
              and w0["txmql"] < w1["txmql"] < w2["txmql"]):
            tag, motivo = "otimiza", (
                f"Tx‑MQL caindo 2 janelas seguidas ({pct(w2['txmql'])} → {pct(w1['txmql'])} → "
                f"{pct(w0['txmql'])}); hipótese: fadiga de criativo/saturação de público/frequência "
                f"alta — investigar antes de cortar."
            )
        elif (w0["cpl"] is not None and w1["cpl"] is not None and w2["cpl"] is not None
              and w0["cpl"] > w1["cpl"] > w2["cpl"]):
            tag, motivo = "otimiza", (
                f"CPL subindo 2 janelas seguidas ({money(w2['cpl'])} → {money(w1['cpl'])} → "
                f"{money(w0['cpl'])}); hipótese: saturação de público/aumento de CPM — revisar segmentação/criativo."
            )
        elif (w0["txmql"] is not None and w1["txmql"] is not None
              and w0["txmql"] >= w1["txmql"] * 0.95):
            tag, motivo = "escala", (
                f"volume {w0['mqls']} MQL(s) ≥ mínimo amostral ({volume_min}) e Tx‑MQL estável/subindo "
                f"({pct(w1['txmql'])} → {pct(w0['txmql'])}) na janela anterior."
            )
        else:
            tag, motivo = "observar", "volume suficiente mas sem 2 janelas comparáveis de Tx‑MQL/CPL ainda."
        out.append((camp, tag, motivo, w0))
    out.sort(key=lambda x: -x[3]["mqls"])
    return out


TAG_LABEL = {"escala": "Escalar", "otimiza": "Otimizar", "corte": "Cortar", "observar": "Observar"}


def bloco_classificacao(camps: list[tuple], meta_cpmql, meta_cac) -> str:
    if not camps:
        return "<p>Sem campanhas com atividade no período.</p>"
    itens = []
    for camp, tag, motivo, w0 in camps[:12]:
        itens.append(
            f'<li><b>{camp}</b> — <span class="tag {tag}">{TAG_LABEL[tag]}</span> — {motivo}</li>'
        )
    aviso = ""
    if meta_cpmql is None and meta_cac is None:
        aviso = ("<p><i>Nenhuma campanha é classificada como Cortar: meta de CPMQL/CAC não está "
                  "definida no painel da aba Relatório. Defina uma meta para habilitar cortes por teto.</i></p>")
    return "<ul>" + "".join(itens) + "</ul>" + aviso


def bloco_gargalo() -> str:
    return (
        "<p><b>Prioridade alta:</b> Agendamentos, Reuniões Realizadas, Vendas e Faturamento não têm "
        "fonte conectada — o funil hoje só vai até MQL. Otimizar mídia sem essas etapas é decisão às "
        "cegas: qualquer corte/escala hoje avalia só qualidade do lead, não qualidade real (comparecimento "
        "e venda). Ação: conectar a lista do comercial (agendamentos/reuniões/vendas) ao dashboard assim "
        "que possível — os campos já existem em `build/app.js` (`agendamentos`/`reunioes`/`vendas`/`fat`) "
        "e acendem a UI automaticamente quando alimentados.</p>"
    )


def bloco_acoes(camps: list[tuple], volume_min: int) -> str:
    escalar = [c for c in camps if c[1] == "escala"]
    otimizar = [c for c in camps if c[1] == "otimiza"]
    observar = [c for c in camps if c[1] == "observar"]
    partes = []
    if escalar:
        nomes = ", ".join(c[0] for c in escalar[:3])
        partes.append(
            f"<p><b>Escalar:</b> {nomes} — aumentar verba em +10–20% a cada 3–4 dias, monitorando "
            f"Tx‑MQL/CPMQL a cada incremento. Não pular direto para saltos maiores: risco de resetar "
            f"o aprendizado do algoritmo de veiculação. Métrica de validação: Tx‑MQL não deve cair "
            f"mais que ~10% após o incremento.</p>"
        )
    if otimizar:
        for camp, tag, motivo, w0 in otimizar[:3]:
            partes.append(
                f"<p><b>Otimizar {camp}:</b> {motivo} Ação: testar novo criativo/ângulo ou revisar "
                f"segmentação nos próximos 3–4 dias; se não recuperar, reduzir verba em ~20% até nova leitura.</p>"
            )
    if observar:
        nomes = ", ".join(c[0] for c in observar[:5])
        partes.append(
            f"<p><b>Observar:</b> {nomes} — manter verba atual, sem decisão de corte/escala até atingir "
            f"o volume mínimo amostral ({volume_min} MQLs).</p>"
        )
    if not partes:
        partes.append("<p>Sem estrutura com dado suficiente para recomendação de ação neste período.</p>")
    return "".join(partes)


def bloco_proxima_decisao(camps: list[tuple], n_dias_corte: int) -> str:
    otimizar = [c for c in camps if c[1] == "otimiza"]
    if otimizar:
        nomes = ", ".join(c[0] for c in otimizar[:3])
        return (
            f"<p><b>Gatilho:</b> {nomes} muda de Otimizar para Escalar se Tx‑MQL voltar a subir por "
            f"2 janelas seguidas, ou para Cortar se CPL continuar subindo por {n_dias_corte} dias "
            f"consecutivos (com meta definida). <b>Prazo:</b> revisar em 4 dias ou ~{money(400.0)} de gasto adicional.</p>"
        )
    return (
        f"<p><b>Gatilho:</b> qualquer campanha atingindo o volume mínimo amostral muda de Observar para "
        f"Escalar/Otimizar conforme Tx‑MQL. <b>Prazo:</b> revisar em 4 dias ou ~{money(400.0)} de gasto adicional.</p>"
    )


def sem_dado_html(label: str) -> str:
    return (
        f"<h3>Resumo do período</h3><p>Sem investimento/atividade registrada em \"{label}\" — nada a reportar "
        f"neste período.</p>"
        f"<h3>Leitura do funil</h3><p>—</p>"
        f"<h3>Classificação por campanha/conjunto</h3><p>—</p>"
        f"<h3>Gargalo de dado — prioridade alta</h3>{bloco_gargalo()}"
        f"<h3>Ações recomendadas</h3><p>Nenhuma ação recomendada sem dado no período.</p>"
        f"<h3>Próxima decisão</h3><p>Reavaliar no próximo período com atividade.</p>"
    )


def build_period_html(label: str, start: date, end: date, meta: list[dict], leads: list[dict],
                       today: date, meta_cpmql, meta_cac, volume_min: int, n_dias_corte: int) -> str:
    cur = derived(agg(meta, leads, start, end))
    if cur["leads"] == 0 and cur["spend"] == 0:
        return sem_dado_html(label)

    ref7 = derived(agg(meta, leads, today - timedelta(days=6), today))
    ref14 = derived(agg(meta, leads, today - timedelta(days=13), today))
    ref30 = derived(agg(meta, leads, today - timedelta(days=29), today))

    camps = classify_campaigns(meta, leads, start, end, volume_min, meta_cpmql, meta_cac, n_dias_corte)

    return (
        f"<h3>Resumo do período</h3>{bloco_resumo(label, cur, ref7, ref14, ref30, meta_cpmql, meta_cac)}"
        f"<h3>Leitura do funil</h3>{bloco_leitura_funil(cur, volume_min)}"
        f"<h3>Classificação por campanha/conjunto</h3>{bloco_classificacao(camps, meta_cpmql, meta_cac)}"
        f"<h3>Gargalo de dado — prioridade alta</h3>{bloco_gargalo()}"
        f"<h3>Ações recomendadas</h3>{bloco_acoes(camps, volume_min)}"
        f"<h3>Próxima decisão</h3>{bloco_proxima_decisao(camps, n_dias_corte)}"
    )


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file")
    ap.add_argument("--meta-file")
    ap.add_argument("--out", default="build/relatorios.json")
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
        "fonte": "Insights de Tráfego gerados automaticamente (regras determinísticas do GUIA-RELATORIOS.md, "
                 "sem chamada de IA) a partir dos dados do funil (mídia paga × Leads).",
        "periodos": {},
    }
    for key, (start, end, label) in periods.items():
        html = build_period_html(
            label, start, end, meta, leads, today,
            bp.META_CPMQL, bp.META_CAC, bp.VOLUME_MIN_AMOSTRAL, bp.N_DIAS_CORTE,
        )
        out["periodos"][key] = {"html": html}

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("== gerar_relatorios ok ==", file=sys.stderr)
    print(f"  periodos gerados: {list(out['periodos'].keys())}", file=sys.stderr)
    print(f"  out: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
