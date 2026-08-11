#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funções puras de datas/agregação compartilhadas entre `gerar_relatorios.py`
(fallback manual, determinístico) e `coletar_dados_relatorio.py` (coleta de
números para a Routine do Claude escrever os Insights). Nenhuma lógica de
texto/interpretação mora aqui — só aritmética sobre os registros brutos de
`build.py` (`leads[]`/`meta[]`).
"""
from __future__ import annotations

from datetime import datetime, timedelta, date

import build as bp

BRT = bp.BRT


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
    """Espelha PRESETS de build/app.js — chaves fixas lidas por relBriefKey()."""
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


def in_range(row_date: str | None, start: date, end: date) -> bool:
    if not row_date:
        return False
    try:
        rd = d(row_date)
    except ValueError:
        return False
    return start <= rd <= end


def agg(meta: list[dict], leads: list[dict], start: date, end: date, camp: str | None = None,
        adset: str | None = None, ad: str | None = None) -> dict:
    def keep(r):
        if not in_range(r["d"], start, end):
            return False
        if camp is not None and r["camp"] != camp:
            return False
        if adset is not None and r["adset"] != adset:
            return False
        if ad is not None and r["ad"] != ad:
            return False
        return True

    m = [r for r in meta if keep(r)]
    l = [r for r in leads if keep(r)]
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
# Formatação (usada pelos templates de texto do gerar_relatorios.py)
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
