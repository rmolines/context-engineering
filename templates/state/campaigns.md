# Campaigns — {Project}

<!--
  Nível OPERACIONAL do sistema de context engineering.
  Conecta o Commander's Intent (CLAUDE.md) às sessões táticas (plans, workstreams).

  Cada campaign traduz uma parte do intent estratégico em um arco de trabalho
  com objetivo mensurável. Campaigns são semi-estáveis: duram semanas/meses,
  não sessões individuais.

  Lido por: /bootstrap (backbrief), /persist (feedback loop)
  Escrito por: usuário (criação), /persist (signals), /bootstrap (sugestão de revisão)

  Cadência de revisão:
  - A cada N sessões (configurável, default ~5)
  - Quando uma campaign é concluída (milestone)
  - Quando signals acumulados indicam divergência do intent
-->

> Last reviewed: {YYYY-MM-DD}
> Review trigger: {cadência | milestone | divergência}

## Active Campaigns

<!--
  Para cada campaign:
  - Intent: o que esta campaign busca alcançar (tradução do Commander's Intent)
  - Connects to: link explícito à seção do CLAUDE.md que justifica esta campaign
  - Success state: definição concreta de "campanha vencida" — quando parar
  - Status: onde estamos agora
  - Signals (INTSUM): dados emergentes da execução — o que as sessões revelaram
    que não era previsto. Estratégia emergente (Mintzberg). Atualizado pelo /persist.

  Exemplo:

  ### C1 — Reduzir tempo de onboarding
  **Intent:** novos devs produtivos em <1 dia (hoje: ~3 dias)
  **Connects to:** Commander's Intent § "developer experience is the product"
  **Success state:** 3 novos devs onboarded em <1 dia sem assistência síncrona
  **Status:** em progresso — docs reescritos, falta automação de setup
  **Signals:**
  - [2026-03-15] devs reportam que o setup local é o maior gargalo, não os docs
  - [2026-03-22] script de bootstrap reduziu setup de 2h pra 15min
-->

### C1 — {nome da campaign}
**Intent:** {o que busca alcançar}
**Connects to:** Commander's Intent § "{trecho relevante}"
**Success state:** {definição concreta de vitória}
**Status:** {not started | em progresso | bloqueado | concluída}
**Signals:**
<!-- Atualizado pelo /persist após cada sessão relevante -->
<!-- Formato: [YYYY-MM-DD] observação emergente da execução -->

## Completed Campaigns

<!--
  Campaigns concluídas com resumo do outcome.
  Manter como registro — informa futuras decisões estratégicas.

  Formato:
  ### C0 — {nome}
  **Outcome:** {o que foi alcançado vs. o que era esperado}
  **Completed:** {YYYY-MM-DD}
  **Key signals:** {os signals mais importantes que surgiram}
-->

## Strategic Review Log

<!--
  Registro de revisões estratégicas — quando o Commander's Intent ou
  as campaigns foram revisados e por quê.

  Formato: [YYYY-MM-DD] {o que mudou e por quê}
  
  Exemplo:
  - [2026-03-01] Criação inicial: 3 campaigns derivadas do intent
  - [2026-03-20] Revisão: C2 cancelada (premissa invalidada por signal de 03-15), C4 criada
-->
