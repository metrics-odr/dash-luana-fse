# CLAUDE.md — Contexto do projeto (template)

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o repositório.
> Ele carrega TODO o contexto necessário para continuar o trabalho sem depender
> de mensagens anteriores. Mantenha-o atualizado.

## ✅ CHECKLIST DE NOVO CLIENTE

Marque cada item ao configurar este template para um cliente novo. Ordem sugerida:

1. **Planilha de dados** (`build/build.py`):
   - [ ] `SPREADSHEET_ID` — ID da planilha Google Sheets (só leitura, export CSV público).
   - [ ] `GID_LEADS` / `GID_META` — gids das abas de Leads e de mídia paga.
   - [ ] Conferir/ajustar os **aliases de coluna** em `header_index()` (nomes de
     cabeçalho podem variar entre clientes) e o **fallback posicional**.
   - [ ] `is_qualified()` — critério de MQL do cliente (ex.: faturamento ≥ X).
   - [ ] `TAX_FACTOR` — imposto/taxa da conta de mídia (1.0 se não houver).
2. **Regra de qualificação em `app.js`** (o critério em `build.py` **não** propaga
   sozinho para textos fixos da UI): revise os rótulos hardcoded "MQLs (≥30k)"
   (2 ocorrências) e a lista `order` de faixas de faturamento (função
   `renderGeralCore`) — ajuste ao critério real do cliente novo.
3. **Branding**: `build/template.html` — troque os dois
   `<<PREENCHER: nome do cliente>>` (`<title>` e logo da sidebar).
4. **Nome do projeto/URL** em `README.md`, `CLAUDE.md` (esta seção "O que é",
   abaixo) e `SETUP-CRON.md` — owner/repo do GitHub e URL do GitHub Pages.
5. **GitHub Pages + Actions**:
   - [ ] Levar `build/` + `.github/workflows/deploy.yml` para a branch `main`
     (o `workflow_dispatch` só existe na branch padrão).
   - [ ] Rodar o workflow uma vez (aba Actions → Run workflow) para o Pages
     habilitar sozinho, ou deixar o cron-job.org disparar a 1ª execução.
6. **cron-job.org** (dispara o build a cada 30 min): siga `SETUP-CRON.md` —
   gerar token fine-grained novo (Actions: read/write, só neste repo), criar o
   job com URL/headers/body do guia. **Nunca** reutilize um token que já
   apareceu em texto puro em algum chat/documento — revogue e gere outro.
7. **Aba Relatório / Insights de Tráfego** (`build/GUIA-RELATORIOS.md`):
   - [ ] Ajustar o contexto do funil (produto/oferta/etapas) no topo do guia.
   - [ ] `build/relatorios.json` começa **vazio** — preencha manualmente
     seguindo o formato do guia, ou plugue uma automação própria (fora do
     escopo deste template: nenhum Worker/Action aqui chama API de IA).
   - [ ] Se for automatizar depois, documente separadamente o novo pipeline
     (cron, secrets do provedor de IA escolhido, prompt).
8. **Teste local** antes de publicar: `python build/build.py --leads-file
   leads.csv --meta-file meta.csv --out dist/index.html` com CSVs de
   amostra; confira as 3 páginas, tema claro/escuro e a multi-seleção.

> Depois de fechar o checklist, apague esta seção ou deixe como referência —
> tanto faz, ela não afeta o build.

---

## O que é

Dashboard de **Captura de Leads** — um app de BI estático (HTML/CSS/JS
puro + Chart.js via CDN) publicado no **GitHub Pages**, que cruza a lista de
**Leads** com o gerenciador de mídia paga e se atualiza sozinho a cada ~30 min
(build 100% na nuvem via GitHub Actions, disparado externamente pelo cron-job.org).

- **URL pública:** `<<PREENCHER: https://<owner>.github.io/<repo>/>>`
- **Somente leitura** das planilhas. Nunca escrever de volta.

## Fontes de dados (Google Sheets)

Spreadsheet ID: `<<PREENCHER: ID da planilha>>` (público — leitura via export CSV).

| Aba | gid | Colunas usadas |
|-----|-----|----------------|
| **Leads** | `<<PREENCHER: gid>>` | `<<PREENCHER: mapeamento de colunas — id/created_time/ad_name/adset_name/campaign_name/is_organic/platform/profissão/critério de qualificação/nome/email/phone>>` |
| **<<PREENCHER: nome da aba de mídia, ex. Meta Ads>>** | `<<PREENCHER: gid>>` | `<<PREENCHER: mapeamento de colunas — Day/Campaign Name/Ad Set Name/Ad Name/Amount Spent/Impressions/Link Clicks/Leads>>` |

URL de export CSV: `https://docs.google.com/spreadsheets/d/<ID>/export?format=csv&gid=<GID>`

### Regra de Lead Qualificado (MQL)
`<<PREENCHER: descreva a regra de qualificação do cliente>>`. (Lógica em `build.py`
→ `is_qualified`; rótulos/ordem de faixas espelhados em `app.js` — ver checklist.)

### Imposto da mídia paga
`<<PREENCHER: se houver imposto/taxa sobre custos da conta de mídia, descreva o
toggle e o fator (ex. ×1,13806 = +13,806%). Se não houver, deixe TAX_FACTOR=1.0
em build.py e remova/ignore o toggle no template.>>`
Constante `TAX_FACTOR` em `build.py` e `TAX` no template.

### Convenções de campanha (do cliente)
`<<PREENCHER: convenções de nomenclatura de campanha do cliente, ex. prefixos por
objetivo/funil, e o mapeamento de UTM (Campaign Name = utm_campaign, etc.)>>`

## Arquitetura / arquivos

```
build/build.py            # lê os 2 CSVs (read-only), emite REGISTROS BRUTOS (leads[]/meta[]/ad_links); render() COSTURA os 4 arquivos abaixo
build/template.html       # esqueleto HTML. Placeholders __STYLES__, __APP_JS__, __DATA_JSON__, __BUILD_ID__, __GENERATED_BRT__
build/identidade-visual.css  # TODAS as cores (tema claro=padrão / escuro). Mexa AQUI p/ trocar só cor
build/estilos.css         # layout/componentes (sidebar, topbar, period-picker, funil, tabelas, gráficos, aba Relatório)
build/app.js              # lógica + renderização (KPIs, funil, tabelas, filtro cruzado, period-picker, heatmap, Relatório)
build/relatorios.json     # Insights de Tráfego por período (aba Relatório) — VERSIONADO; lido no build, sem API. Vem VAZIO neste template.
build/GUIA-RELATORIOS.md  # guia de métricas do funil + como redigir os Insights da aba Relatório
.github/workflows/deploy.yml  # roda build.py e publica no Pages (workflow_dispatch + schedule + push)
dist/index.html           # saída gerada (gitignored; o Actions reconstrói)
GUIA-REPLICACAO.md        # como replicar este modelo para outros relatórios/clientes
SETUP-CRON.md             # valores exatos do cron-job.org (com marcadores a preencher)
```

### Aba Relatório
Terceira página (sidebar, entre a de mídia paga e o rodapé). **Espelha a Visão
Geral** (mesmo funil/KPIs/gráficos/tabela diária, via `renderGeralCore(REL_IDS)`)
e, abaixo, acrescenta 3 blocos novos + um painel de metas editável:
- **Metas & parâmetros (painel editável)** — no topo da aba: Meta CPMQL, Meta CAC, Volume
  mínimo amostral (MQLs), N dias p/ corte. Persiste em `localStorage['dm_metas']`, default de
  `build.py` (`META_CPMQL`/`META_CAC`=None → "não definida"; `VOLUME_MIN_AMOSTRAL`/`N_DIAS_CORTE`).
  Editar recolore **CPMQL/CAC** nas tabelas de anúncio (verde ≤ meta · amarelo até +30% ·
  vermelho acima) e ajusta o badge Em observação/Avaliável (usa o volume mínimo), **tudo ao vivo**
  (`METAS` + `renderRelAds()` em `app.js`, sem re-render dos gráficos).
- **Top Anúncios** e **Piores Anúncios** — 22 colunas + coluna **Status** (Anúncio · Status ·
  Campanha · Conjunto · Gasto · Impr · CPM · CTR · Leads · CPL · MQLs · Tx‑MQL · CPMQL · Check‑ins ·
  Tx‑Check‑in · CPCIN · Presenças · CPP · Vendas · CAC · Faturamento · ROAS · **Link**). Anúncio,
  Status e Link ficam **sticky** (visíveis sem rolar). Ranking pelo **resultado mais profundo
  disponível** (Venda→Presença→Check‑in→MQL), amostra relevante primeiro; sem amostra → badge
  **"Em observação"** (nunca "vencedor"/"ruim" por 1 resultado ou por CTR/CPM/CPL isolados).
  Limiares em `build.py`: `SAMPLE_MIN_SPEND`, `SAMPLE_MIN_MQLS`, `TOP_ADS_N`. Scroll lateral
  **contido na tabela** (`.rel-adt` → `table-layout:auto`).
- **Insights de Tráfego** — texto por período no formato de analista de performance
  (foco em ação), lido de `build/relatorios.json` (sem API no build/navegador). 6 blocos
  fixos: Resumo (com comparação 7/14/30 d) · Leitura do funil · Classificação por
  campanha/conjunto (tag + critério numérico) · **Gargalo de dado (prioridade alta)**
  · Ações (com %, R$, dias) · Próxima decisão (gatilho + prazo). Cita a meta ou sinaliza
  "meta não definida". Chaves de período fixas (`hoje/ontem/3d/7d/14d/30d/mes/mespass/todo`), tags
  `Escalar/Otimizar/Cortar/Observar`. Regras completas em `build/GUIA-RELATORIOS.md`. **Este
  template não inclui automação de geração por IA** — `relatorios.json` vem vazio; preencha
  manualmente ou plugue sua própria automação (ver checklist no topo deste arquivo).

Funil completo (ajuste as etapas ao cliente): `Impressões → Cliques → Leads → MQLs →
Check-ins → Presenças → Vendas → Faturamento`. Enquanto só houver mídia paga × Leads, o
funil vai até MQL; Check-ins/Presenças/Vendas/Fat aparecem "-" até chegar a lista do
comercial/evento — quando os campos `checkins`/`presencas`/`vendas`/`fat` forem somados
em `buildAgg/daily/totals`, `salesOf()` acende tudo sozinho.

### Link do criativo (aba de mídia paga)
`build.py` lê uma coluna opcional de permalink do criativo na aba de mídia →
mapa `ad_links` (anúncio → 1 permalink). Usado no "Link" das tabelas Top/Piores
(abre em nova aba). Sem a coluna, o link vira "—".

> **Layout modular:** o front-end é separado em `identidade-visual.css` + `estilos.css`
> + `app.js`, costurados por `render()` nos placeholders `__STYLES__`/`__APP_JS__`.
> Página 1 usa **funil vertical de leads** (Gasto → Impressões → Cliques → Leads →
> MQLs → Vendas/Faturamento "-") + KPIs secundários. Topbar tem **seletor de período
> em calendário** (period-picker). **Heatmap** das tabelas diárias = cor FIXA por
> métrica (só opacidade varia): **Gasto=vermelho · Leads=azul · MQLs=verde**
> (`--heat-gasto/leads/mqls`), aplicado só nessas 3 colunas.

O `build.py` **não agrega**: exporta as linhas cruas e TODA a lógica (filtros de
data, filtro cruzado, KPIs, tabelas, gráficos, heatmap, imposto) roda no navegador.
Isso permite interatividade total sem servidor.

## Rodar/testar local

```bash
python build/build.py --leads-file leads.csv --meta-file meta.csv --out dist/index.html
# (o sandbox do agente NÃO alcança docs.google.com; use CSVs locais para testar.
#  O runner do GitHub Actions tem internet e busca os CSVs ao vivo.)
```
Para conferir o visual sem depender do CDN: baixe `chart.js@4.4.1` do npm, troque a
`<script src=...>` por um caminho local e rode um screenshot com Chromium headless.

## Especificação funcional (resumo)

Três **páginas separadas** (sidebar, sem rolar entre elas):
1. **Visão Geral de Leads** — **funil vertical** (Gasto → Impressões → Cliques → Leads →
   MQLs → Vendas/Faturamento = "-", com CPM/CTR/CPC/CPL/ConvForm/Tx‑MQL/CPMQL inline) +
   **KPIs secundários**; gráfico combinado diário colado à **tabela diária com
   heatmap (todos os leads)**; barras por origem/faixa/plataforma/profissão.
2. **Captura mídia paga** — funil em etapas; combinado diário; barras por utm_content;
   **tabela diária com heatmap (só mídia paga)**; **3 tabelas hierárquicas** Campanha →
   Conjunto → Anúncio, cada uma com **gráfico de linha colado embaixo**.
3. **Relatório** — espelha a Visão Geral e acrescenta **painel de Metas editável** +
   **Top Anúncios · Piores Anúncios** (22 colunas + Status, com link do criativo) +
   **Insights de Tráfego** (texto de `relatorios.json`, foco em ação). Ver seção
   "Aba Relatório" acima e `build/GUIA-RELATORIOS.md`.

**Ordem das colunas nas tabelas de heatmap/hierarquia:**
`Data · Dia · Gasto · CPM · CTR · ConvForm(=Leads/Cliques) · Leads · CPL · Tx‑MQL · MQLs · CPMQL`
(nas hierárquicas a 1ª coluna é a dimensão em vez de Data/Dia).

**Regras obrigatórias das tabelas** (ver `GUIA-REPLICACAO.md`): cabeçalho sticky;
ordenação tri‑state (asc→desc→reset); colunas redimensionáveis (persist localStorage);
linha "Total Geral" fixa; dimensão nunca truncada (400/250/600px, wrap, ≥11px);
seleção com toggle + **Ctrl multi (Set/OR)**; **filtro cruzado bidirecional** com
âncora Anúncio>Conjunto>Campanha, reconstruindo tudo da fonte filtrada; tabela diária
com **último dia no topo**. **Heatmap de cor fixa por métrica** (só a opacidade varia,
maior valor = mais vibrante), aplicado apenas em **Gasto (vermelho) · Leads (azul) ·
MQLs (verde)** — cores em `--heat-gasto/leads/mqls`. As demais colunas ficam sem heatmap.

## Lacunas de dados (comuns até o cliente enviar mais fontes)
- **Vendas, Faturamento, ROAS, CAC** → precisam de uma aba de compradores (gid a
  informar), com utm_source/produto.
- **Page Views, CR, CPV, ConvLP** → precisam de uma fonte de page views.
- Enquanto não vierem, essas métricas aparecem como "-".

## Publicação — como resolver os problemas conhecidos

1. **Push:** se a integração GitHub da sessão for somente‑leitura (`git push` e as
   MCP tools derem 403 "Resource not accessible by integration"), o caminho que
   funciona é `git push` direto para `github.com` usando o **PAT do usuário** (o
   proxy permite o túnel git bruto; a API REST do Actions/Pages costuma ser
   bloqueada). Nunca gravar o token no `.git/config` (usar URL efêmera
   `https://x-access-token:<TOKEN>@github.com/...`).
2. **cron-job.org só funciona na `main`:** `workflow_dispatch` só existe quando o
   workflow está na branch padrão. Levar `build/` + `.github/workflows/deploy.yml` para
   a `main` para ativar.
3. **Pages liga sozinho:** `actions/configure-pages@v5` com `enablement: true`
   habilita o Pages na 1ª execução (precisa `permissions: pages: write, id-token: write`).
4. **Proxy do sandbox:** o ambiente do agente costuma NÃO alcançar `docs.google.com`,
   `*.github.io` nem a API REST de Actions/Pages — mas o runner do GitHub Actions
   alcança tudo. Testar dados via CSV local; confiar no Actions para o resto.
5. **Token exposto:** se um token/PAT foi colado no chat, avisar para **revogar e
   gerar um novo** (fine‑grained, só Actions: read/write neste repo).

## Branch / git
- `<<PREENCHER: branch de desenvolvimento deste cliente>>`; manter sincronizada com `main`.
