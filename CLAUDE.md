# CLAUDE.md — Markdown Viewer

## What This Is
A lightweight Tkinter-based Markdown document viewer for vintage PowerPC Macs (OS X 10.4+). It renders `.md` files as styled rich text in a native GUI window — no web browser or external dependencies beyond Python 2.5's standard library.

## Tech Stack
- **Python 2.5** (compatible with 2.4+; uses only stdlib)
- **Tkinter** — GUI framework (tk.Text widget with tagged segments for rich rendering)
- **No external dependencies** — fully self-contained with what ships on Mac OS X

## Project Structure
```
viewer.py                       # Main app: Tkinter GUI, file loading, rendering, zoom, keybindings
markdown_parser.py              # MarkdownParser class: block + inline Markdown → tagged segments
README.md                       # Project documentation
Markdown Viewer.app/            # Mac .app bundle wrapper
  Contents/
    Info.plist                  # Bundle metadata; registers .md/.markdown/.mdown/.txt file types
    PkgInfo                     # APPLMdVw bundle type+signature
    MacOS/
      MarkdownViewer            # Bash launcher script → cd to Resources, runs `python viewer.py`
    Resources/
      appicon.icns              # Application icon
      viewer.py                 # (copy of viewer.py)
      markdown_parser.py        # (copy of parser)
```

## How to Run
```bash
# Open with welcome screen
python viewer.py

# Open a specific file
python viewer.py README.md

# Or double-click "Markdown Viewer.app" in Finder
```

## Architecture

### markdown_parser.py
- **`MarkdownParser`** class with one public method:
  - **`parse(text)`** — Parses Markdown into a flat list of `(text, [tag1, tag2, ...])` tuples. Handles: fenced code blocks, ATX + Setext headings, horizontal rules, unordered/ordered lists, blockquotes, blank lines, and normal paragraphs.
  - **`_parse_inline(text, segments, base_tags)`** — Called internally for inline formatting within blocks. Finds earliest match among patterns (bold+italic, bold, italic, inline code, strikethrough) and recurses. Inline matches get their style tags merged with the block's base tags.

### viewer.py
- **`MarkdownViewer`** class — the entire GUI app:
  - `_setup_fonts()` — Creates font objects; detects available families (Lucida Grande / Helvetica, Monaco / Courier) with fallbacks
  - `_setup_menu()` — Native Mac menu bar (File, Edit, View menus with accelerators)
  - `_setup_tags()` — Configures Tkinter Text widget tags: h1–h6, normal, bold, italic, bold_italic, code_inline, code_block, list_bullet, list_item, blockquote, blockquote_bar, hr, strikethrough
  - `_render(markdown_text)` — Parses via `MarkdownParser.parse()`, inserts tagged segments into Text widget
  - `_resolve_tags(tags)` — Merges `bold` + `italic` into `bold_italic` tag
  - `open_file(filepath)` / `cmd_reload()` / `cmd_open()` — File I/O; status bar shows filename, line count, file size
  - `cmd_zoom_in()` / `cmd_zoom_out()` / `cmd_zoom_reset()` — Zoom by adjusting font sizes ±2pt (min 8pt)
  - `_show_welcome()` — Renders a built-in Markdown welcome message when no file is loaded
- **`main()`** — Entry point; creates Tk root, optionally loads file from `sys.argv[1]`

## Key Conventions & Patterns
- **Python 2 style throughout**: `object` base classes, `except IOError, e:` syntax, `print` as statement, `%` string formatting, `Tkinter` / `tkFont` / `tkFileDialog` / `tkMessageBox` imports.
- **No HTML rendering** — all display via Tkinter Text widget tags, not a web view.
- **Self-contained** — zero third-party dependencies; only Python 2.5 stdlib.
- **Tag-based styling**: Parser returns `(text, [tags])` tuples; viewer inserts text with those tags. Tags can be combined (e.g. bold text inside a list item gets both `bold` and `list_item` tags).
- **Zoom** works by directly mutating `tkFont.Font` objects' size (±2pt per step), which automatically updates all widgets using those fonts — no re-render needed.
- **Font fallbacks**: Tries Lucida Grande → Helvetica → TkDefaultFont; Monaco → Courier → TkFixedFont.
- **Color constants** as class attributes on `MarkdownViewer`: `BG_COLOR`, `TEXT_COLOR`, `ACCENT_COLOR`, `CODE_BG`, `BLOCKQUOTE_COLOR`, `HR_COLOR`.
- **Mac .app bundle**: Bash launcher script in `MacOS/MarkdownViewer` runs Python from `Resources/` dir. Bundle registers for .md, .markdown, .mdown, .txt file types.
- **UI has 3 zones**: toolbar (file path label), main Text widget with scrollbar, status bar (filename, lines, size).

## Keyboard Shortcuts
| Shortcut | Action       |
|----------|--------------|
| Cmd+O    | Open file    |
| Cmd+R    | Reload file  |
| Cmd+W    | Close window |
| Cmd+=    | Zoom in      |
| Cmd+-    | Zoom out     |
| Cmd+0    | Reset zoom   |
| Cmd+A    | Select all   |
| Cmd+C    | Copy         |