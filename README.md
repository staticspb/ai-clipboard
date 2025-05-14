# AI Clipboard

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/)
[![OpenRouter](https://img.shields.io/badge/backend-OpenRouter.ai-green)](https://openrouter.ai)

**AI Clipboard** is a lightweight Windows utility that connects your system clipboard to powerful language models via OpenRouter.  
Just copy text starting with a prefix like `AI:` — and get the AI-generated response automatically returned to your clipboard.

---

## Features

- Fast and automatic clipboard monitoring
- Multi-model support via [OpenRouter](https://openrouter.ai/)
- Optional system instructions (global prompt behavior)
- Context support via `.md` files for knowledge injection
- Configurable prefix, refresh interval, and model shortcuts
- Tray icon with hide/show functionality
- Light and dark mode support (auto-detect)

---

## Example Usage

Copy any of the following to your clipboard:

```

AI:Translate this to French
AI:gpt:Summarize this text
AI:@legal:Summarize contract key terms
AI:claude:@legal:Summarize NDA document

````

- `gpt` is a model shortcut you define
- `@legal` references a Markdown file `knowledge/legal.md`

---

## Screenshots

**Light mode**

![Light Mode](https://raw.githubusercontent.com/staticspb/ai-clipboard/refs/heads/master/screenshots/screenshot-light.png)

**Dark mode**

![Dark Mode](https://raw.githubusercontent.com/staticspb/ai-clipboard/refs/heads/master/screenshots/screenshot-dark.png)

---

## Installation

1. Clone or download the repository  
2. Run `ai-clipboard.pyw` with Python 3.11+  
3. On first run, configuration and cache folders are created:
   - `config/config.json`
   - `cache/models_cache.json`
   - `logs/ai_clipboard.log`

Dependencies:
- `requests`, `tkinter`, `pyperclip`, `pystray`, `sv_ttk`, `darkdetect`, `Pillow`, `winsound`

You can install them via:

```bash
pip install -r requirements.txt
````

---

## Configuration

Settings are stored in `config/config.json`:

* `base_url`: API endpoint (default is `"https://openrouter.ai/api/v1"`)
* `api_key`: Your OpenRouter API key
* `prefix`: Trigger prefix for clipboard commands (e.g., `"AI:"`)
* `clipboard_refresh_interval`: How often the clipboard is checked (in ms, minimum `100`)
* `default_model`: Model used when no shortcut is specified
* `model_shortcuts`: Mapping of shortcut names to full model IDs
* `custom_system_instruction`: Optional system prompt to override model behavior
* `use_custom_prompt`: Whether to apply the custom system instruction
* `balance_usd`: Approximate API usage cost (auto-updated)

---

## Keyboard Shortcut Logic

Format:
`prefix[:shortcut][:@context]:prompt`

Examples:

* `AI:hello` → sent to default model
* `AI:gpt:hello` → sent to model shortcut `gpt`
* `AI:@docs:explain this` → sent with context from `docs.md`

---

## License

MIT License — see `LICENSE` file for details.

---

## Contributions

Pull requests are welcome. Please open issues or discussions before major changes.