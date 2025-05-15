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

Here’s a README section explaining the compiled version and how users can extract or build their own EXE from the source code:

---

## AI Clipboard - Compiled Version

We have made it easy for you to use **AI Clipboard** as a standalone Windows executable (EXE). The **compiled** version of the app can be found in the `compiled` directory of this repository.

### How to Use the Precompiled EXE

1. **Download the ZIP**:

   * Download the ZIP file `AI-Clipboard-Py-2-Exe.zip` from the `compiled` directory.

2. **Extract the Files**:

   * Extract the contents of the ZIP file to a location of your choice.

3. **Run the EXE**:

   * Inside the extracted folder, you will find `AI Clipboard.exe`. Double-click it to run the application.
   * The following directories should be kept next to the `AI Clipboard.exe` file:

     * `icons/`: Contains the application icon.
     * `knowledge/`: Contains example `.md` files.
     * `sounds/`: Contains required `.wav` files for notifications and toasts.

   Ensure that the directory structure is maintained, so the application can access all the necessary resources.

### How to Build Your Own EXE from Source Code

If you would like to build your own version of the **AI Clipboard** EXE, follow these steps:

1. **Install Required Dependencies**:

   * Make sure you have Python installed on your system.
   * Install the necessary Python packages by running:

     ```
     pip install -r requirements.txt
     ```

2. **Install PyInstaller**:

   * Install PyInstaller, which is used to create the EXE:

     ```
     pip install pyinstaller
     ```

3. **Compile the EXE**:

   * Open a command prompt or terminal window and navigate to the project directory.
   * Run the following PyInstaller command to compile the script:

     ```
     pyinstaller --noconfirm --onedir --console --icon "path\to\icon.ico" --name "AI Clipboard" --upx-dir "path\to\UPX" "path\to\ai-clipboard.pyw"
     ```

     Replace the paths with the correct directories on your system. Ensure that you specify:

     * `--icon` to point to the `.ico` file.
     * `--upx-dir` to point to your UPX directory (if you're using UPX to compress the EXE).

4. **Retrieve Your EXE**:

   * After PyInstaller finishes, you will find the compiled `AI Clipboard.exe` in the `output` folder.

5. **Organize the Files**:

   * Place the following directories alongside the EXE:

     * `icons/` — The icon directory with your `icon.ico`.
     * `knowledge/` — The directory containing your knowledge files (e.g., `.md` files).
     * `sounds/` — The directory containing the `.wav` files.

6. **Test Your EXE**:

   * Run the generated EXE to ensure that everything works as expected.

---

## License

MIT License — see `LICENSE` file for details.

---

## Contributions

Pull requests are welcome. Please open issues or discussions before major changes.