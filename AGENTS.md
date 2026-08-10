# AGENTS.md — Template de dashboard de captura de leads

> Contexto completo em **`CLAUDE.md`** (mesma pasta) — leia-o antes de mexer no
> projeto. Este arquivo é um resumo para agentes/ferramentas que seguem a
> convenção `AGENTS.md`.

## ✅ CHECKLIST DE NOVO CLIENTE (resumo — detalhes em CLAUDE.md)

1. `build/build.py`: `SPREADSHEET_ID`, `GID_LEADS`, `GID_META`, aliases de coluna
   em `header_index()`, `is_qualified()` (critério de MQL), `TAX_FACTOR`.
2. `build/app.js`: revisar os rótulos "MQLs (≥30k)" e a lista `order` de faixas
   de faturamento — o critério de `build.py` não propaga sozinho para esses
   textos fixos da UI.
3. `build/template.html`: substituir o nome do cliente no `<title>` e no logo.
4. `README.md` / `CLAUDE.md` / `SETUP-CRON.md`: owner/repo do GitHub, URL do
   GitHub Pages, nome do cliente.
5. GitHub Pages + Actions: levar `build/` + `.github/workflows/deploy.yml`
   para a `main` (ativa `workflow_dispatch`); rodar o workflow uma vez.
6. cron-job.org: seguir `SETUP-CRON.md` — token fine-grained novo (Actions:
   read/write, só neste repo), nunca reaproveitar um token exposto em chat.
7. Aba Relatório / Insights de Tráfego (`build/GUIA-RELATORIOS.md`): ajustar o
   contexto do funil; `build/relatorios.json` começa vazio — preencher manual
   ou plugar automação própria (não incluída neste template: nenhum
   Worker/Action aqui chama API de IA).
8. Testar local com CSVs de amostra antes de publicar (3 páginas, tema
   claro/escuro, multi-seleção).

## Engine (não muda entre clientes)
`build/template.html`, `build/app.js`, `build/estilos.css`,
`.github/workflows/deploy.yml`, `GUIA-REPLICACAO.md` — tabelas, filtros,
gráficos, heatmap, tema claro/escuro. Ver `GUIA-REPLICACAO.md` para os detalhes
de implementação (filtro cruzado, engine de tabela, gráficos Chart.js).

## Específico do cliente (troca a cada replicação)
`build/build.py`, `build/identidade-visual.css` (cores), `build/relatorios.json`
(conteúdo), `build/GUIA-RELATORIOS.md` (contexto do funil), `README.md`,
`CLAUDE.md`, `SETUP-CRON.md`.
