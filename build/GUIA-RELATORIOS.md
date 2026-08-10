# GUIA — Insights de Tráfego da aba Relatório

> Texto lido de `build/relatorios.json` pela aba **Relatório** (seção "Insights
> de Tráfego"). **Não faz nenhuma chamada de API no build nem no navegador** —
> a página só exibe o texto já pronto. Os números vêm dos mesmos dados do site
> (mídia paga × Leads); quem escrever o texto (você, um analista, ou uma
> automação de IA que você configurar depois) apenas **interpreta e redige**.
> A aba Relatório espelha a Visão Geral e, abaixo, mostra **Top Anúncios ·
> Piores Anúncios · Insights de Tráfego**.

## Como preencher `build/relatorios.json`

Este template **não inclui automação de geração por IA** (nenhum workflow,
Worker ou script chama uma API de LLM). O arquivo `build/relatorios.json` vem
vazio (9 chaves de período, `html:""`) e é lido pelo build normalmente — sem
esse conteúdo, a aba mostra tudo (cards/tabelas/gráficos) menos os Insights.

Para preencher: edite `build/relatorios.json` manualmente (ou plugue uma
automação própria — GitHub Action + qualquer API de IA, rodando antes do
`deploy.yml`) seguindo o formato e as regras deste guia, faça commit na
`main`. Se quiser automatizar depois, documente separadamente o novo pipeline
(cron, secrets, prompt) — isso está fora do escopo deste template.

## Contexto do funil

<<PREENCHER: descreva em 1-2 parágrafos o funil e o produto/oferta deste
cliente (ex.: evento presencial, lançamento, infoproduto, SaaS...) e o que
qualifica um lead como MQL>>. Fluxo genérico (ajuste as etapas ao cliente):

```
Impressões → Cliques/abertura do formulário → Leads → MQLs → Check-ins → Presenças → Vendas → Faturamento
```

- **MQL** = <<PREENCHER: critério de qualificação do cliente>> (ver `build.py`
  → `is_qualified`).
- **Check-in** = vaga confirmada pelo comercial **antes** do evento (se aplicável).
- **Presença** = comparecimento efetivo, validado no local (se aplicável).

> **Estado atual dos dados:** enquanto só houver mídia paga × Leads, o funil
> vai até **MQL**. As etapas seguintes (Check-ins, Presenças, Vendas,
> Faturamento) e as métricas derivadas aparecem como “-” até chegar a lista do
> comercial/evento/vendas. Quando os campos `checkins`/`presencas`/`vendas`/
> `fat` forem somados por linha em `buildAgg/daily/totals` (`build/app.js`),
> **toda a UI acende sozinha** (funil, tabelas, Top/Piores).

## Fórmulas fundamentais

- **Tx MQL** = MQLs ÷ Leads · **CPMQL** = Investimento ÷ MQLs
- **Tx Check-in** = Check-ins ÷ MQLs · **CPCIN** = Investimento ÷ Check-ins
- **Tx Presença** = Presenças ÷ Check-ins · **CPP** = Investimento ÷ Presenças
- **Tx Venda** = Vendas ÷ Presenças · **CAC** = Investimento ÷ Vendas
- **ROAS** = Faturamento ÷ Investimento · **Ticket** = Faturamento ÷ Vendas
- Conversões acumuladas úteis: Lead→Check-in, Lead→Presença, Lead→Venda,
  MQL→Presença, MQL→Venda, Check-in→Venda.

Regra de ouro: **acumulativas somam** (impressões, cliques, leads, MQLs, gasto);
**derivadas recalculam dos totais** (nunca some percentuais).

## Princípio de interpretação

Trate cada métrica como **diagnóstico probabilístico**, nunca regra absoluta.
Uma métrica ruim raramente identifica sozinha a causa. Leia **sempre** com a etapa
anterior e a posterior, o histórico, o **volume da amostra** e o **tempo de
maturação**. O objetivo não é o menor CPL nem o maior volume de leads — é gerar
leads qualificados que avancem no funil até a venda.

**CPMQL, CPCIN, CPP, CAC e ROAS são resultados acumulados (efeito), não causas.**
Ao ver um deles ruim, aponte a **etapa** que perdeu eficiência — não recomende
"reduzir o CAC/CPP/ROAS" de forma abstrata.

### Leitura por etapa (resumo)
- **CTR** (Cliques/Impressões): interesse do criativo. CTR baixo **pode ser bom**
  se qualifica melhor (CPMQL/CPP/CAC saudáveis). Só é problema junto de custo ruim.
- **CPL**: custo do cadastro. CPL alto pode ser saudável se gera mais MQL/presença.
  CPL baixo pode ser ruim se atrai gente fora do ICP.
- **Tx MQL / CPMQL**: mídia+criativo+form atraindo o perfil certo. Tx alta com
  pouco volume pode ser segmentação estreita ou critério permissivo — o MQL só
  vale se avançar para check-in, presença e venda.
- **Tx Check-in / CPCIN**: qualidade do MQL + atratividade da oferta + eficiência
  do comercial (tempo até 1º contato, taxa de contato, tentativas, script).
- **Tx Presença / CPP**: compromisso após a confirmação (reconfirmação, lembretes,
  logística, valor percebido). **CPP é uma das principais métricas operacionais.**
- **Tx Venda / CAC / Ticket / ROAS**: qualidade real da oferta + pitch +
  follow-up + maturação (venda high-ticket costuma fechar dias depois).

### Heurísticas obrigatórias
- CTR baixo + CPMQL/CPP/CAC saudáveis → o anúncio qualifica melhor (não mexer).
- CPL baixo + Tx MQL baixa → mídia atraindo fora do ICP.
- Tx MQL boa + Tx Check-in baixa → investigar **comercial**/disponibilidade/script,
  não o tráfego automaticamente.
- Tx Check-in boa + Tx Presença baixa → confirmação/lembretes/logística.
- Tx Presença boa + Tx Venda baixa → oferta/pitch/follow-up
  (sala cheia ≠ sala qualificada).
- CPMQL bom + CPCIN ruim → perda entre qualificação e confirmação.
- CPCIN bom + CPP ruim → perda entre confirmação e comparecimento.
- CPP bom + CAC ruim → perda entre evento e venda.
- Evento/lançamento recente + ROAS baixo → verificar **maturação** antes de julgar.
- Só uma campanha piorou → investigar a própria (segmentação/criativo), não geral.

## Top Anúncios e Piores Anúncios (o que a tabela já faz)

A aba calcula sozinha, por anúncio (com gasto no período):
- **Top**: ranqueado pelo **resultado mais profundo disponível** (Venda → Presença →
  Check-in → MQL), maior volume + menor custo, **amostra relevante primeiro**.
  Anúncio promissor **sem amostra suficiente** entra marcado **"Em observação"** —
  nunca é "vencedor" só por 1 resultado com pouco gasto.
- **Piores**: só anúncios com **investimento relevante** e resultado profundo
  fraco / custo pior que a média; **nunca** por CTR/CPM/CPL isolados. Sem amostra
  suficiente → **"Em observação"**, não "ruim".
- Limiares em `build.py`: `SAMPLE_MIN_SPEND`, `SAMPLE_MIN_MQLS`, `TOP_ADS_N`.
- **Link** abre o criativo (coluna opcional de permalink na aba de mídia →
  `ad_links`).

O texto deve **explicar** o ranking (por quê), não repeti-lo.

## Formato "Insights de Tráfego" (por período) — foco em AÇÃO

> O tom é de **analista de performance**: cada período fecha com decisão, não
> só leitura de número. Português, profundo mas sem enrolação. **Sempre** use
> exatamente estes 5–6 blocos, nesta ordem (cada um é um `<h3>`):

1. **Resumo do período** — números brutos (gasto, leads, MQLs, Tx‑MQL, CPL, CPMQL)
   **+ comparação obrigatória contra as janelas de 7, 14 e 30 dias**. Toda métrica
   citada vem com referência: a **meta/teto** da conta **ou**, se não definida, a
   comparação com o próprio histórico + o aviso **"meta não definida"** (nunca deixe
   um número sem referência de bom/ruim). Abra com a linha de status das metas.
2. **Leitura do funil** — o que está **funcionando**, o que é **ruído por volume
   baixo** (e quantos MQLs/dias/R$ faltam para virar amostra confiável), e o que é
   **gargalo de dado**. Nunca conclua nada abaixo do volume mínimo amostral.
3. **Classificação por campanha/conjunto** — `<ul>` onde **cada** estrutura recebe
   obrigatoriamente **uma das 4 tags** com o **critério numérico** que levou a ela:
   - **`Escalar`** — volume ≥ mínimo amostral **E** Tx‑MQL estável/subindo nas 2
     últimas janelas.
   - **`Observar`** — volume < mínimo amostral; **informe** o gasto/dias que faltam
     até volume suficiente.
   - **`Otimizar`** — volume suficiente, mas Tx‑MQL caindo **ou** CPL subindo por 2
     janelas consecutivas; **aponte a hipótese** (fadiga de criativo, saturação de
     público, frequência alta, mudança de qualificação) antes de generalizar.
   - **`Cortar`** — volume suficiente, **zero** conversão qualificada, e CPL/CPMQL
     acima do **teto** por **N dias** consecutivos (N do painel; padrão 5). **Cortar
     exige meta/teto definido** — se a meta não estiver preenchida, não classifique
     nada como Cortar; diga que depende de definir a meta.
4. **Gargalo de dado — prioridade alta** — sempre que uma etapa (check‑in, presença,
   venda, faturamento) **não tiver fonte conectada**, isso é um item de ação próprio,
   **separado** dos gargalos de campanha, com prioridade alta (otimizar sem essa
   etapa é decisão às cegas). Enquanto o funil só for até MQL, este bloco existe em
   todos os períodos.
5. **Ações recomendadas** — com **números concretos** (%, R$, dias). Para escala,
   recomende o **tamanho do incremento** (ex.: +10–20% a cada 3–4 dias) e **alerte
   sobre resetar o aprendizado** se o salto for maior. Cada ação diz: o que fazer,
   em qual estrutura/etapa, quais métricas justificam, resultado esperado e a
   métrica de validação.
6. **Próxima decisão** — **gatilho** (o que muda a classificação de cada campanha)
   **+ prazo/gasto** para revisitar (ex.: "revisar em 4 dias ou ~R$ 600 de gasto").

Ao citar um anúncio (ex. "AD05"), **sempre** diga a campanha (e o conjunto quando
ajudar) — o mesmo nome de anúncio pode rodar em campanhas diferentes.

### Metas & parâmetros (painel editável da aba)
O gestor preenche no topo da aba: **Meta CPMQL**, **Meta CAC**, **Volume mínimo
amostral (MQLs)** e **N dias p/ corte**. Defaults em `build.py` (`META_CPMQL`,
`META_CAC` = None → "não definida"; `VOLUME_MIN_AMOSTRAL`, `N_DIAS_CORTE`). As
tabelas de anúncio **recoram CPMQL/CAC** vs meta (verde ≤ meta · amarelo até
+30% · vermelho acima) e o badge **Em observação/Avaliável** usa o volume
mínimo — tudo ao vivo. O texto dos Insights **cita a meta (ou "meta não
definida")** e usa o volume mínimo/N dias configurados como critério das
classificações. Se `META_CPMQL`/`META_CAC` estiverem None, escreva comparando
contra as janelas 7/14/30 d e sinalize que a meta não foi definida.

## Comparações e segurança analítica

Compare o período com: período anterior de mesma duração; média histórica;
metas; outras campanhas/conjuntos/anúncios. Ao apontar variação, mostre valor
atual, anterior, variação absoluta e %, e o impacto no funil. **Não invente**
métricas/benchmarks; **não** trate ausência de dado como zero; **não** compare
janelas de maturação diferentes; **não** penalize leads recentes ainda não
trabalhados; **não** recomende cortar/escalar com amostra insuficiente; **não**
culpe o tráfego por perda que acontece depois do MQL, nem o comercial se o MQL
estiver ruim.

## Formato de `build/relatorios.json`

```json
{
  "generated_at": "DD/MM/AAAA HH:MM",
  "fonte": "Gerado a partir dos dados do funil (mídia paga × Leads).",
  "periodos": {
    "hoje":    {"html": "<h3>Resumo do período</h3><p>…</p><h3>Leitura do funil</h3><p>…</p><h3>Classificação por campanha/conjunto</h3><ul>…</ul><h3>Gargalo de dado — prioridade alta</h3><p>…</p><h3>Ações recomendadas</h3><p>…</p><h3>Próxima decisão</h3><p>…</p>"},
    "ontem":   {"html": "…"},
    "3d":      {"html": "…"},
    "7d":      {"html": "…"},
    "14d":     {"html": "…"},
    "30d":     {"html": "…"},
    "mes":     {"html": "…"},
    "mespass": {"html": "…"},
    "todo":    {"html": "…"}
  }
}
```

- **Chaves de período fixas** (mesmos ids do seletor da topbar). O texto só
  aparece nos períodos predefinidos; em intervalo personalizado ou dias
  selecionados a aba mostra uma mensagem orientando a escolher um preset.
- HTML permitido no `html`: `<h3> <p> <ul> <li> <b>` e
  `<span class="tag escala|otimiza|corte|observar">Escalar|Otimizar|Cortar|Observar</span>`
  (a classe de "Otimizar" é `otimiza`, não `otimizar`).
- Se um período não tiver dados, escreva um `html` curto dizendo que não houve
  investimento/atividade. Se o arquivo não existir ou vier vazio (como no
  template), a aba mostra tudo menos os Insights (cards/tabelas seguem
  funcionando).
