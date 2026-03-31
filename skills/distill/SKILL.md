---
name: distill
description: "Cristaliza um fluxo da sessão atual em skill nova ou atualização de skill existente. Analisa o que foi feito, extrai o padrão repetível, identifica anti-patterns aprendidos, e formaliza tudo. Usar quando um fluxo manual deu certo e vale ser reutilizável. Triggers: 'distill', 'cristaliza isso', 'formaliza esse fluxo', 'transforma em skill', 'quero reusar isso', 'salva esse workflow'."
---

# Distill

Transforma um fluxo que aconteceu na sessão em conhecimento reutilizável.

**Input:** `<descrição opcional>` — o que destilar. Se omitido, analisa a sessão inteira.

## Filosofia

1. **O melhor momento pra formalizar é agora** — enquanto o contexto tá fresco na conversa
2. **Update > Create** — se já existe uma skill que cobre 80% do fluxo, atualiza ela em vez de criar outra
3. **Anti-patterns valem ouro** — o que deu errado e foi corrigido é mais valioso que o que funcionou de cara
4. **Skill ≠ memory** — skill é processo (como fazer), memory é contexto (o que sei). Separar bem

## Fluxo

### Fase 1: Análise da sessão (inline)

Reler a conversa e identificar:

1. **Workflow executado** — sequência de passos que foi feita (quais skills/ferramentas, em que ordem)
2. **Iterações de refinamento** — onde o primeiro output não serviu e o que foi ajustado
3. **Decisões de design** — escolhas que não eram óbvias mas deram certo
4. **Anti-patterns descobertos** — o que deu errado e por quê
5. **Defaults que funcionaram** — valores/padrões que deviam ser o default desde o início

Apresentar ao usuário:

```
## Destilação — [nome do fluxo]

### Workflow identificado
1. Passo A → Passo B → Passo C

### O que funcionou de cara
- ...

### O que precisou de iteração (oportunidade de melhoria)
- Problema: ...
- Fix: ...
- Regra: ...

### Anti-patterns aprendidos
- Nunca ...
- Sempre ...

### Proposta
- [ ] Criar skill nova: `/nome` — [escopo]
- [ ] Atualizar skill existente: `/nome` — [o que muda]
- [ ] Salvar feedback em memory — [o que]
```

Esperar aprovação antes de prosseguir.

### Fase 2: Execução (após aprovação)

Dependendo da proposta aprovada:

**Se criar skill nova:**
1. Definir scope da skill (global `~/.claude/skills/` ou projeto `.claude/skills/`)
2. Escrever `SKILL.md` com frontmatter completo
3. Incluir seções: Filosofia, Fluxo (com fases), Anti-patterns, Arquivos de referência
4. A description do frontmatter deve incluir triggers naturais em PT-BR e EN

**Se atualizar skill existente:**
1. Ler a skill atual
2. Adicionar novos anti-patterns à seção de anti-patterns
3. Atualizar checklists com novos items
4. Ajustar defaults que mudaram
5. Não remover o que já existe — só adicionar/refinar

**Se salvar feedback em memory:**
1. Criar/atualizar arquivo em `memory/`
2. Atualizar `MEMORY.md`
3. Seguir formato: regra + Why + How to apply

### Fase 3: Campaign awareness

**Executar apenas se** `.claude/state/campaigns.md` existe E contém campaigns ativas.

1. Ler campaigns ativas em `.claude/state/campaigns.md`
2. O fluxo destilado avança alguma campaign? O aprendizado (anti-patterns, defaults) é relevante pra alguma?
3. Se sim → incluir na proposta da Fase 1:
   - `- [ ] Registrar signal em campaign C{N}: {observação}`
4. Se aprovado → adicionar signal datado na campaign relevante:
   ```
   - [YYYY-MM-DD] Distill: {o que o fluxo revelou sobre a campaign}
   ```
5. Se o fluxo destilado sugere uma nova direção não coberta por campaigns → mencionar como possível estratégia emergente

### Fase 4: Validação

- Reler o que foi escrito/atualizado
- Confirmar que o fluxo da sessão seria reproduzível por outra sessão seguindo a skill
- Verificar que os anti-patterns estão claros e acionáveis

## Heurísticas

### Quando criar skill nova vs. atualizar existente

| Sinal | Ação |
|-------|------|
| 70%+ do fluxo já existe numa skill | Atualizar |
| Fluxo totalmente novo, sem skill relacionada | Criar nova |
| Duas skills foram combinadas de forma nova | Criar skill de composição (que orquestra as duas) |
| O aprendizado é sobre como usar uma skill, não o que ela faz | Salvar como feedback/memory |

### O que NÃO destilar

- Fluxos one-off que não vão se repetir
- Conhecimento que já está no código (ler o código é mais confiável que uma skill desatualizada)
- Preferências pessoais que já estão em `CLAUDE.md` (não duplicar)
- Detalhes de implementação que mudam rápido (ex: "o arquivo X fica na linha 42")

### Qualidade de uma boa skill

Uma skill destilada deve ter:
- **Fases claras** — cada fase com input/output definido
- **Checklists** — items verificáveis, não genéricos
- **Anti-patterns** — "nunca faça X porque Y"
- **Pontos de validação** — onde parar e confirmar com o usuário
- **Arquivos de referência** — paths concretos pra onde olhar
