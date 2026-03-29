# TUI Frameworks e Técnicas de Visualização Terminal
> Pesquisa: 2026-03-27

## Frameworks — comparativo

### Textual (Python)

Estado: ativo, v0.80+, by Textualize (Will McGugan, mesmo criador do Rich).

- CSS-like styling com `tcss` (Textual CSS), incluindo flexbox-style layout
- Asyncio nativo — sem threading manual pra maioria dos casos
- 120 FPS via delta-update (só renderiza o que mudou)
- Widgets prontos: DataTable, ProgressBar, Sparkline, Log, Tree, Input, Button, TextArea
- `set_interval(n, callback)` pra polling periódico sem bloqueio
- Workers (`@work(thread=True)`) pra I/O bloqueante em background
- Textual Web: serve o mesmo app no browser sem mudança de código
- Mouse support, dark/light mode, animações

**Layout proporcional** (essencial pro nosso caso):
```css
/* fr units — como CSS Grid */
#item-a { height: 5fr; }  /* 5/10 da tela */
#item-b { height: 3fr; }  /* 3/10 da tela */
#item-c { height: 2fr; }  /* 2/10 da tela */
```

Também suporta `%`, valores absolutos, e recalcula dinamicamente em runtime.

**Performance com updates a 1-2s**: zero problema. Event loop asyncio + delta rendering projetado pra isso.

Padrão pra I/O bloqueante:
```python
@work(thread=True, exclusive=True)
def fetch_data(self) -> None:
    result = blocking_io_call()
    self.call_from_thread(self.update_ui, result)

def on_mount(self) -> None:
    self.set_interval(2, self.fetch_data)
```

### Ink (Node.js)

Estado: ativo, 28k+ stars, v4.x. Usado por GitHub Copilot CLI, Gatsby, Prisma, Shopify.

- JSX normal renderizado no terminal via Yoga (engine Flexbox do Facebook)
- Modelo mental idêntico ao React — componentes, hooks, estado reativo
- Layout proporcional via `flexDirection="column"` + `flexGrow={1}`
- Real-time via hooks do React (useState, useEffect) + useStdin
- True Color via chalk, barras de progresso via ink-progress-bar
- JSON de stdin direto via useStdin + JSON.parse
- Não usar console.log enquanto Ink renderiza — quebra layout

### Bubbletea (Go)

Estado: 41k stars, mantido pela Charm. v2 em desenvolvimento (alpha/beta 2025).

- Elm Architecture: Model (estado), Init(), Update(msg), View()
- Layout via lipgloss: JoinVertical, Width(), Height() — mais manual que Flexbox
- Real-time via tea.Cmd — comandos async retornam msgs que atualizam modelo
- True Color via lipgloss (16/256/True Color)
- Componentes prontos via bubbles: progress bar, spinner, text input, viewport, table, list
- JSON de stdin via Cmd + json.Unmarshal

Ecossistema Charm completo:
| Lib | Função | Stars |
|---|---|---|
| Bubbletea | Framework TUI (Elm arch) | 41k |
| Lipgloss | Styling CSS-like | 10.9k |
| Bubbles | Componentes prontos | — |
| Gum | Componentes shell-scriptable | 23k |
| Glow | Markdown renderer terminal | 24k |

### Ratatui (Rust)

Estado: framework TUI mais popular em Rust, fork comunitário do tui-rs (2023). Muito ativo.

- Immediate-mode rendering — a cada frame descreve toda a UI, Ratatui renderiza o diff
- Controle total do loop principal
- Layout: `Layout::vertical` com Constraint::Percentage, Constraint::Ratio, Constraint::Fill
- Real-time via loop manual, threads/tokio, 60+ FPS
- Widgets nativos: Gauge, Sparkline, BarChart, LineChart, tabelas, scrollable lists
- True Color (RGB), estilos inline
- JSON via serde_json no loop principal
- 30-40% menos memória e 15% menos CPU que Bubbletea equivalente

### Blessed / Neo-Blessed (Node.js)

**Não recomendado.** Praticamente abandonado. Incompatibilidades com Node.js recente. Comunidade migrou pra Ink.

### Tabela comparativa

| Critério | Textual (Python) | Ink (Node) | Bubbletea (Go) | Ratatui (Rust) |
|---|---|---|---|---|
| Layout proporcional | CSS `fr` nativo | Flexbox nativo | Lipgloss, manual | Constraint nativo |
| Real-time updates | set_interval async | React state | tea.Cmd async | Loop manual |
| Cores/Unicode | Sim (Rich) | Sim (chalk) | Sim (lipgloss) | Sim (True Color) |
| Progress bars | Widget nativo | ink-progress-bar | bubbles/progress | Gauge nativo |
| JSON stdin | File read + parse | useStdin + parse | Cmd + Unmarshal | serde_json no loop |
| Performance | Boa | Boa | Muito boa | Excelente |
| Manutenção 2026 | Ativa | Ativa | Muito ativa | Muito ativa |
| Curva aprendizado | Baixa (CSS) | Baixa (React) | Média (Elm) | Alta (Rust) |

## Técnicas de visualização em terminal

### Unicode block characters

Progressão de resolução disponível:

**Block Elements (U+2580–U+259F)** — 1×1 por célula:
```
▁▂▃▄▅▆▇█   (U+2581–U+2588) — 8 níveis verticais
░▒▓█        (U+2591–U+2588) — densidade crescente
```

**Braille Patterns (U+2800–U+28FF)** — 2×4 por célula:
```
256 combinações, resolução 2× horizontal, 4× vertical por célula
Usado por drawille (Python/Go), btop++, Ratatui charts
```

**Sextants (U+1FB00–U+1FBFF)** — 2×3 por célula:
```
64 combinações, Unicode 13 (2020)
Usado por Notcurses, btop++. Exigem fonte com cobertura.
```

### Box drawing characters

```
Simples:    ┌─┬─┐     Arredondado: ╭─┬─╮
            │ │ │                   │ │ │
            ├─┼─┤                   ├─┼─┤
            └─┴─┘                   ╰─┴─╯

Pesados:    ┏━┳━┓     Duplos:      ╔═╦═╗
            ┃ ┃ ┃                   ║ ║ ║
            ┗━┻━┛                   ╚═╩═╝
```

Ranges: U+2500–U+257F (Box Drawing), U+2580–U+259F (Block Elements), U+25A0–U+25FF (Geometric Shapes).

### Sparklines

Algoritmo básico:
```python
BLOCKS = " ▁▂▃▄▅▆▇█"  # 9 níveis (0–8)

def sparkline(values):
    mn, mx = min(values), max(values)
    span = mx - mn or 1
    return "".join(BLOCKS[round((v - mn) / span * 8)] for v in values)

sparkline([2, 5, 1, 8, 3, 7])  → "▂▄▁█▂▇"
```

### Representação proporcional

Para blocos que ocupam espaço proporcional a um valor:

```python
def proportional_block(value, total, available_rows):
    filled_rows = round(value / total * available_rows)
    full = "█" * terminal_width
    empty = "░" * terminal_width
    return "\n".join([full] * filled_rows + [empty] * (available_rows - filled_rows))
```

Precisão de 1/8 de linha com block elements:
```python
EIGHTHS_V = " ▁▂▃▄▅▆▇█"

def smooth_bar(value, total, rows):
    exact = value / total * rows * 8  # em oitavos
    full_rows = int(exact) // 8
    partial = int(exact) % 8
    # renderiza full_rows completas + 1 parcial + restante vazio
```

### Técnicas de rendering real-time

**Alternate screen** — ocupa tela sem destruir scrollback:
```
\x1b[?1049h  → entra (como htop, vim, lazygit)
\x1b[?1049l  → sai e restaura tela original
```

**Synchronized output** — elimina flicker (vsync pra terminal):
```
\x1b[?2026h  → begin synchronized update
... escreve frame inteiro ...
\x1b[?2026l  → end synchronized update (exibe atomicamente)
```
Suportado em: kitty, WezTerm, foot, Alacritty, iTerm2.

**Double buffering em software** (quando terminal não suporta sync):
1. Renderiza frame inteiro em buffer de string
2. Diff com frame anterior (only dirty cells)
3. Escreve apenas diferenças com posicionamento de cursor
4. Ratatui implementa isso nativamente

**Cursor control essencial:**
```
\x1b[H          → home (1,1)
\x1b[{r};{c}H   → posição (r,c)
\x1b[?25l       → oculta cursor
\x1b[?25h       → exibe cursor
```

### Virtual scrolling

Nunca renderiza conteúdo completo — mantém viewport deslizante:

```python
class VirtualScroll:
    def __init__(self, items, viewport_height):
        self.items = items
        self.height = viewport_height
        self.offset = 0

    def scroll(self, delta):
        self.offset = max(0, min(
            self.offset + delta, len(self.items) - self.height
        ))

    def visible_items(self):
        return self.items[self.offset : self.offset + self.height]
```

Scrollbar proporcional:
```
posição do thumb = (offset / total_items) * viewport_height
tamanho do thumb = (viewport_height / total_items) * viewport_height
```

## Projetos de referência

| Projeto | Stack | Relevância |
|---|---|---|
| btop++ | C++, braille patterns | Gráficos com blocos proporcionais, referência de UX |
| bandwhich | Rust + Ratatui | Barras de uso por processo, layout adaptativo |
| lazygit / lazydocker | Go + gocui | Painéis com box drawing, navegação vim-style |
| k9s | Go + tview | Layout em tabelas e painéis full-screen |
| Notcurses | C | Máxima fidelidade gráfica, auto-detecta blitter |
| posting | Python + Textual | HTTP client TUI, referência de app Textual bem construído |
| Glances | Python + curses | Monitor tipo htop |

## Recomendação pro nosso caso

Para um visualizador que lê JSON (statusline + log de contexto) e renderiza lista vertical de blocos:

**Textual** é a escolha pragmática:
- Layout proporcional com `fr` units é exatamente o que precisamos
- `set_interval` pra polling sem complexidade
- Python permite iteração rápida
- Não precisa de 60fps — 1-2s de refresh é suficiente
- Pode rodar no browser via Textual Web (bonus)

**Bubbletea** se quiser distribuir como binário Go leve.

**Ratatui** se performance importar (não importa aqui — polling a 1-2s não exige 60fps).

## Fontes
- [Textual — site oficial](https://textual.textualize.io/)
- [Textual — Layout Guide](https://textual.textualize.io/guide/layout/)
- [Textual — smooth scrolling](https://textual.textualize.io/blog/2025/02/16/smoother-scrolling-in-the-terminal-mdash-a-feature-decades-in-the-making/)
- [Textual — algorithms for high performance](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/)
- [GitHub — vadimdemedes/ink](https://github.com/vadimdemedes/ink)
- [GitHub — charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea)
- [GitHub — charmbracelet/lipgloss](https://github.com/charmbracelet/lipgloss)
- [Ratatui — site oficial](https://ratatui.rs/)
- [GitHub — ratatui/ratatui](https://github.com/ratatui/ratatui)
- [GitHub — aristocratos/btop](https://github.com/aristocratos/btop)
- [GitHub — imsnif/bandwhich](https://github.com/imsnif/bandwhich)
- [GitHub — jesseduffield/lazydocker](https://github.com/jesseduffield/lazydocker)
- [GitHub — rothgar/awesome-tuis](https://github.com/rothgar/awesome-tuis)
- [ANSI escape codes — gist completo](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797)
- [Build your own CLI with ANSI escape codes — Li Haoyi](https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html)
- [Synchronized Output spec](https://gist.github.com/christianparpart/d8a62cc1ab659194337d73e399004036)
- [Go vs Rust for TUI — DEV Community](https://dev.to/dev-tngsh/go-vs-rust-for-tui-development-a-deep-dive-into-bubbletea-and-ratatui-2b7)
- [Rich — Live Display](https://rich.readthedocs.io/en/latest/live.html)
- [drawille — pixel graphics via braille](https://github.com/asciimoo/drawille)
