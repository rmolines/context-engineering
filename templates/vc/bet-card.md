# Bet: {{startup_name}}
<!-- Template for GitHub Issue in the VC portfolio project -->
<!-- Labels: bet:active | Milestone: [C5] VC-Founder Architecture (or dedicated fund milestone) -->

## Thesis

{{why_this_bet_makes_sense}}
One sentence: what does this startup do and why does it deserve investment?

## Strategy

- **North Star Metric:** {{north_star_metric}}
- **Where to play:** {{segment_market_niche}}
- **How to win:** {{differentiator_moat}}
- **Full strategy:** `.claude/state/fund/bets/{{slug}}/strategy.md`
- **Current cycle plan:** `.claude/state/fund/bets/{{slug}}/cycles/cycle-{{N}}.md`

## Startup

- **Repo:** {{repo_url}}
- **Stage:** {{early / mvp / growing}}
- **What exists today:** {{current_state_of_the_repo}}

## Investment terms

- **Runway:** {{N}} runs
- **Check-in cadence:** Board meeting every {{M}} runs
- **Retro cadence:** Every 5 runs (founder writes)
- **Schedule:** Every {{X}} hours via Cloud Scheduled Task
- **Founder model:** claude-{{model-name}}

## Cycle Key Results

| KR | Baseline | Target | Kill threshold |
|---|---|---|---|
| {{kr_1}} | {{baseline}} | {{target}} | {{kill_if_below}} |
| {{kr_2}} | {{baseline}} | {{target}} | {{kill_if_below}} |
| {{kr_3}} | {{baseline}} | {{target}} | {{kill_if_below}} |

## Scope

**Founder CAN:**
- {{allowed_1}}
- {{allowed_2}}

**Founder CANNOT (without VC approval):**
- {{forbidden_1}}
- {{forbidden_2}}

## Kill criteria

- [ ] Runway reaches 0 with no renewal
- [ ] {{custom_criterion_1}}
- [ ] {{custom_criterion_2}}

## Progress log

<!-- Board meeting summaries are posted as comments on this Issue -->
<!-- Founder Run Reports are also posted as comments -->
<!-- Founder Retros are posted as comments every 5 runs -->
<!-- VC Directives: post a comment starting with "## VC Directive" -->

---
*Managed by CE /spawn, /board, /fund skills*
