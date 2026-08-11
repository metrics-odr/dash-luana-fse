# GUIA — Insights de Tráfego da aba Relatório

> Texto lido de `build/relatorios.json` pela aba **Relatório** (seção "Insights
> de Tráfego"). **Não faz nenhuma chamada de API no build nem no navegador** —
> a página só exibe o texto já pronto. Os números vêm dos mesmos dados do site
> (mídia paga × Leads); quem escreve o texto (hoje, uma Routine do Claude —
> ver seção abaixo) apenas **interpreta e redige**.
> A aba Relatório espelha a Visão Geral e, abaixo, mostra **Top Anúncios ·
> Piores Anúncios · Insights de Tráfego**.
>
> **Este guia define o FORMATO/estrutura do texto.** As regras de
> **diagnóstico** (como interpretar cada métrica, quando um número ruim não é
> problema, o que analisar junto do quê) estão em
> `build/GUIA-INTERPRETACAO-METRICAS.md` — leitura obrigatória antes de
> redigir qualquer período.

## Como `build/relatorios.json` é gerado (pipeline atual: Routine do Claude)

`build/relatorios.json` é escrito 1×/dia às **23:59 BRT** por uma **Routine
do Claude** (Claude Code Remote), não por uma chamada à API da Anthropic —
é a mesma infraestrutura de sessão/agente usada neste repositório, só
agendada. O fluxo tem 2 etapas, porque o ambiente onde a Routine roda não
alcança `docs.google.com` (só o runner do GitHub Actions alcança):

1. **Coleta de números (determinística, GitHub Actions)** —
   `build/coletar_dados_relatorio.py` lê os CSVs (mídia paga × Leads) e
   agrega **só aritmética** (totais, comparativos 7/14/30d e vs. período
   anterior, quebra por campanha/conjunto/anúncio com série diária) em
   `build/relatorios_dados.json`. Roda via `.github/workflows/briefing.yml`
   (1×/dia, 23:50 BRT, + `workflow_dispatch` manual) e commita direto na
   `main`. **Não é lido pelo site** — é só insumo intermediário.
2. **Redação dos Insights (Claude, Routine agendada)** — 9 minutos depois,
   uma sessão do Claude lê `build/relatorios_dados.json` +
   `build/GUIA-RELATORIOS.md` (este arquivo, formato/estrutura) +
   `build/GUIA-INTERPRETACAO-METRICAS.md` (regras de diagnóstico por
   métrica) e escreve `build/relatorios.json` — o texto final, no formato
   descrito abaixo — e faz commit/push direto na `main`, o que dispara o
   `deploy.yml` e republica o dashboard.

Testar a coleta de números manualmente:

```bash
python build/coletar_dados_relatorio.py --leads-file leads.csv --meta-file meta.csv --out build/relatorios_dados.json
```

`build/gerar_relatorios.py` (o gerador **determinístico**, sem IA, mais raso)
continua no repo como **fallback manual** — não roda mais automaticamente.
Se a Routine falhar num dia, rode-o pra garantir que a aba não fique vazia:

```bash
python build/gerar_relatorios.py --leads-file leads.csv --meta-file meta.csv --out build/relatorios.json
```

`build/relatorios.json` também pode ser editado à mão seguindo o mesmo
formato — o build só lê o arquivo, não importa como foi gerado. Se o arquivo
não existir ou vier vazio, a aba mostra tudo (cards/tabelas/gráficos) menos
os Insights.

## Contexto do funil

**Funil de Sessão Estratégica (FSE)** — Luana Ferreira, Negócio com Alma. É um
funil de **venda 1:1 por reunião** (não evento/lançamento): o anúncio no Meta
Ads leva a uma página de formulário (typeform) que faz perguntas qualificatórias
— a principal é a faixa de faturamento declarada — e, se qualificado, o lead
**agenda uma reunião** (Sessão Estratégica/Diagnóstica) com a equipe comercial,
onde a oferta é apresentada e a venda acontece.

```
Impressões → Cliques/abertura do formulário → Leads → MQLs (QLF) → Agendamentos → Reuniões Realizadas → Vendas → Faturamento
```

- **MQL / QLF** = faturamento médio mensal declarado pelo lead **≥ R$ 5.000** (ver
  `build.py` → `is_qualified`).
- **Agendamento** = o lead qualificado marcou horário de reunião com o comercial.
- **Reunião Realizada** = a reunião de fato aconteceu (o lead compareceu). O
  inverso disso é o **No‑Show** (agendou e não compareceu) — a métrica de alerta
  mais importante entre Agendamento e Venda.

> **Estado atual dos dados:** enquanto só houver mídia paga × Leads, o funil
> vai até **MQL**. As etapas seguintes (Agendamentos, Reuniões Realizadas, Vendas,
> Faturamento) e as métricas derivadas aparecem como “-” até chegar a lista do
> comercial/vendas. Quando os campos `agendamentos`/`reunioes`/`vendas`/
> `fat` forem somados por linha em `buildAgg/daily/totals` (`build/app.js`),
> **toda a UI acende sozinha** (funil, tabelas, Top/Piores).

## Fórmulas fundamentais

- **Tx MQL** = MQLs ÷ Leads · **CPMQL** = Investimento ÷ MQLs
- **Tx Agendamento** = Agendamentos ÷ MQLs · **CPAG** = Investimento ÷ Agendamentos
- **Tx NS** = No-Shows÷ Agendamentos · **CPNS** = Investimento ÷ No-Shows
- **No‑Show** = 1 − (Reuniões Realizadas ÷ Agendamentos) · **CPRR** = Investimento ÷ Reuniões Realizadas
- **Tx Venda** = Vendas ÷ Reuniões Realizadas · **CAC** = Investimento ÷ Vendas
- **ROAS** = Faturamento ÷ Investimento · **Ticket** = Faturamento ÷ Vendas
- Conversões acumuladas úteis: Lead→Agendamento, Lead→Reunião Realizada, Lead→Venda,
  MQL→Reunião Realizada, MQL→Venda, Agendamento→Venda.

Regra de ouro: **acumulativas somam** (impressões, cliques, leads, MQLs, gasto);
**derivadas recalculam dos totais** (nunca some percentuais).

## Princípio de interpretação

Trate cada métrica como **diagnóstico probabilístico**, nunca regra absoluta.
Uma métrica ruim raramente identifica sozinha a causa. Leia **sempre** com a etapa
anterior e a posterior, o histórico, o **volume da amostra** e o **tempo de
maturação**. O objetivo não é o menor CPL nem o maior volume de leads — é gerar
leads qualificados que avancem no funil até a venda.

**CPMQL, CPAG, CPRR, CAC e ROAS são resultados acumulados (efeito), não causas.**
Ao ver um deles ruim, aponte a **etapa** que perdeu eficiência — não recomende
"reduzir o CAC/CPRR/ROAS" de forma abstrata.

### Leitura por etapa (resumo)
- **CTR** (Cliques/Impressões): interesse do criativo. CTR baixo **pode ser bom**
  se qualifica melhor (CPMQL/CPRR/CAC saudáveis). Só é problema junto de custo ruim.
- **CPL**: custo do cadastro. CPL alto pode ser saudável se gera mais MQL/reunião.
  CPL baixo pode ser ruim se atrai gente fora do ICP.
- **Tx MQL / CPMQL**: mídia+criativo+form atraindo o perfil certo (passou pelas
  perguntas qualificatórias de renda). Tx alta com pouco volume pode ser
  segmentação estreita ou critério permissivo — o MQL só vale se avançar para
  agendamento, reunião realizada e venda.
- **Tx Agendamento / CPAG**: qualidade do MQL + atratividade da oferta de
  reunião + eficiência do comercial (tempo até 1º contato, taxa de contato,
  tentativas, script de agendamento).
- **No‑Show / CPRR**: compromisso do lead após agendar (lembrete, remarcação,
  horário, valor percebido da reunião). **No‑Show é uma das principais métricas
  operacionais** — reunião marcada e não realizada é dinheiro parado no meio do funil.
- **Tx Venda / CAC / Ticket / ROAS**: qualidade real da oferta + pitch da reunião +
  follow-up + maturação (venda high-ticket costuma fechar dias depois da reunião).

### Heurísticas obrigatórias
- CTR baixo + CPMQL/CPRR/CAC saudáveis → o anúncio qualifica melhor (não mexer).
- CPL baixo + Tx MQL baixa → mídia atraindo fora do ICP.
- Tx MQL boa + Tx Agendamento baixa → investigar **comercial**/disponibilidade/script
  de agendamento, não o tráfego automaticamente.
- Tx Agendamento boa + No‑Show alto → lembrete/confirmação/horário/remarcação —
  o problema é entre marcar e comparecer, não a qualificação do lead.
- Reunião Realizada boa (No‑Show baixo) + Tx Venda baixa → oferta/pitch/follow-up
  da reunião (agenda cheia ≠ agenda qualificada).
- CPMQL bom + CPAG ruim → perda entre qualificação e agendamento.
- CPAG bom + No‑Show alto (CPRR ruim) → perda entre agendamento e comparecimento.
- CPRR bom + CAC ruim → perda entre reunião realizada e venda.
- Reunião/lançamento recente + ROAS baixo → verificar **maturação** antes de julgar.
- Só uma campanha piorou → investigar a própria (segmentação/criativo), não geral.

## Top Anúncios e Piores Anúncios (o que a tabela já faz)

A aba calcula sozinha, por anúncio (com gasto no período):
- **Top**: ranqueado pelo **resultado mais profundo disponível** (Venda → Reunião
  Realizada → Agendamento → MQL), maior volume + menor custo, **amostra relevante primeiro**.
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

> O tom é de **gestor de tráfego experiente falando com outro gestor**:
> profundo na análise, mas linguagem simples e direta — técnico **só** quando
> for indispensável para justificar a conclusão. Cada período fecha com
> decisão, não só leitura de número. Antes de redigir qualquer bloco, leia
> por inteiro `build/GUIA-INTERPRETACAO-METRICAS.md` e aplique suas
> heurísticas: **nunca julgue uma métrica isolada** — leia sempre junto com a
> etapa anterior e a posterior do funil, compare com o histórico da própria
> conta (usando a série diária/comparativos de `relatorios_dados.json`) e,
> quando fizer sentido, com os benchmarks gerais de mercado do guia
> (deixando claro que é referência do nicho, não dado medido deste cliente).
> **Sempre** use exatamente estes 7 blocos, nesta ordem (cada um é um `<h3>`):

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
4. **Gargalo de dado — prioridade alta** — sempre que uma etapa (agendamento,
   reunião realizada, venda, faturamento) **não tiver fonte conectada**, isso é
   um item de ação próprio, **separado** dos gargalos de campanha, com
   prioridade alta (otimizar sem essa etapa é decisão às cegas). Enquanto o
   funil só for até MQL, este bloco existe em todos os períodos.
5. **Ações recomendadas** — com **números concretos** (%, R$, dias). Para escala,
   recomende o **tamanho do incremento** (ex.: +10–20% a cada 3–4 dias) e **alerte
   sobre resetar o aprendizado** se o salto for maior. Cada ação diz: o que fazer,
   em qual estrutura/etapa, quais métricas justificam, resultado esperado e a
   métrica de validação.
6. **Próxima decisão** — **gatilho** (o que muda a classificação de cada campanha)
   **+ prazo/gasto** para revisitar (ex.: "revisar em 4 dias ou ~R$ 600 de gasto").
7. **Briefing do Gestor** — resumo executivo corrido (parágrafos, sem enrolação,
   pronto para copiar/enviar ao cliente ou ler em voz alta numa reunião),
   cobrindo na ordem:
   - **O que aconteceu** no período: leitura geral do funil (gasto → leads →
     MQLs) e comparação com o histórico (7/14/30d e período anterior de
     mesmo tamanho) em uma frase de abertura.
   - **Diagnóstico com profundidade** — pelo menos 2–4 insights aplicando as
     heurísticas do `GUIA-INTERPRETACAO-METRICAS.md` (diagnóstico
     probabilístico, métrica lida junto da anterior/posterior, "isso é bom
     mesmo parecendo ruim" ou vice-versa), no mesmo espírito destes
     exemplos:
     - *"CTR do anúncio X está baixo, mas o CAC/Tx-MQL segue saudável — não é
       problema, é qualificação melhor."*
     - *"O CPM subiu em quase todas as campanhas — parece leilão mais caro em
       geral (ver se coincide com data comemorativa), não um problema de
       criativo específico."*
     - *"O Connect Rate do funil caiu abaixo do normal — investigar antes se
       é mensuração (pixel/CAPI) ou página, olhando se leads/MQLs também
       caíram junto."*
   - **Sinalização de mercado**: quando uma métrica estiver fora do padrão
     geral do nicho High Ticket (ex.: Connect Rate crítico <60%), citar isso
     explicitamente como leitura de mercado, não só comparação interna.
   - **Recomendações de corte/escala nomeadas** — cada recomendação cita a
     estrutura específica (campanha, conjunto **ou** anúncio, pelo nome) e o
     número que justifica (ex.: "escalar o conjunto XPTO +20% de verba: CPMQL
     R$X, abaixo da média da conta em Y%"; "copiar os anúncios XYZ — CAC caindo
     há 3 dias, hoje rodam só na campanha Z — para uma estrutura de escala,
     ex. CBO com os Top Ads").
   - Fecha com 1 frase de prioridade: qual é a ÚNICA coisa mais importante a
     decidir/fazer com base neste período.

   Este bloco é o único dos 7 com foco em **prosa corrida** (parágrafos), não
   em listas técnicas — os blocos 1–6 continuam objetivos/estruturados; o
   Briefing do Gestor é a síntese em linguagem de gestão.

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
  "fonte": "Insights de Tráfego redigidos pelo Claude (Routine diária, 23h59 BRT) a partir dos números agregados em relatorios_dados.json (mídia paga × Leads).",
  "periodos": {
    "hoje":    {"html": "<h3>Resumo do período</h3><p>…</p><h3>Leitura do funil</h3><p>…</p><h3>Classificação por campanha/conjunto</h3><ul>…</ul><h3>Gargalo de dado — prioridade alta</h3><p>…</p><h3>Ações recomendadas</h3><p>…</p><h3>Próxima decisão</h3><p>…</p><h3>Briefing do Gestor</h3><p>…</p>"},
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
  (a classe de "Otimizar" é `otimiza`, não `otimizar`). O bloco "Briefing do
  Gestor" usa só `<p>`/`<b>` (prosa corrida, sem `<ul>`).
- Se um período não tiver dados, escreva um `html` curto dizendo que não houve
  investimento/atividade. Se o arquivo não existir ou vier vazio (como no
  template), a aba mostra tudo menos os Insights (cards/tabelas seguem
  funcionando).
