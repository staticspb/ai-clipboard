"""
AI Clipboard
==========================================

A clipboard monitoring utility with AI integration using OpenRouter.

Author: Vakhtang Gegechkori (staticspb)
License: MIT
Repository: https://github.com/staticspb/ai-clipboard
Version: 1.2.0
"""

import sys
import locale
import pywinstyles
import json, os, re, time, threading, tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import pyperclip, requests, logging
import pystray
from pystray import MenuItem as item, Menu
from PIL import Image
import winsound
import sv_ttk
import darkdetect

VERSION = '1.2'
FONT_FAMILY = 'Segoe UI Emoji'
FONT_SIZE = 10
CONFIG_PATH = 'config.json'
CACHE_PATH = 'models_cache.json'

def ensure_folders_exist():
	os.makedirs("config", exist_ok=True)
	os.makedirs("logs", exist_ok=True)
	os.makedirs("cache", exist_ok=True)
	os.makedirs("sounds", exist_ok=True)
	os.makedirs("icons", exist_ok=True)

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)
		
def load_config():
	default = {
		"base_url": "https://openrouter.ai/api/v1",
		"api_key": "",
		"prefix": "AI:",
		"clipboard_refresh_interval": 500,
		"custom_system_instruction": "You are a direct response AI assistant. Follow these rules strictly:\n1. Provide ONLY the direct answer/solution - no introductions, disclaimers, or conclusions\n2. For code requests, provide ONLY the code with minimal necessary comments\n3. Never ask questions back\n4. Never add explanations unless explicitly requested\n5. Never add pleasantries or signatures\n6. Keep responses concise and to the point",
		"use_custom_prompt": False,
		"default_model": "openai/gpt-4o-mini",
		"model_shortcuts": {},
		"balance_usd": 0.0
	}
	if os.path.exists(os.path.join("config", CONFIG_PATH)):
		with open(os.path.join("config", CONFIG_PATH), 'r', encoding='utf-8') as f:
			return json.load(f)
	return default

def save_config(cfg):
	with open(os.path.join("config", CONFIG_PATH), 'w', encoding='utf-8') as f:
		json.dump(cfg, f, indent=2)

class ToastNotifier:
	def __init__(self, theme, root=None):
		self.theme = theme
		self.root = root

	def notify(self, title, message, timeout=3000):
		def show_toast():
			is_dark = self.theme == "dark"
			bg_color = "#333333" if is_dark else "#f0f0f0"
			fg_color = "white" if is_dark else "black"
			close_color = "white" if is_dark else "black"

			# Create a hidden root for toast (won't take focus)
			toast_root = tk.Tk()
			toast_root.withdraw()

			toast = tk.Toplevel(toast_root)
			toast.overrideredirect(True)
			toast.attributes("-topmost", True)
			toast.attributes("-alpha", 0.95)
			toast.attributes("-toolwindow", True)
			toast.attributes("-disabled", False)

			screen_width = toast.winfo_screenwidth()
			screen_height = toast.winfo_screenheight()
			width, height = 380, 120
			x = screen_width - width - 30
			y = screen_height - height - 30
			toast.geometry(f"{width}x{height}+{x}+{y}")
			toast.configure(bg=bg_color)

			frame = tk.Frame(toast, bg=bg_color)
			frame.pack(fill="both", expand=True, padx=10, pady=10)

			tk.Button(
				toast,
				text="✕",
				command=toast.destroy,
				bd=0,
				bg=bg_color,
				fg=close_color,
				activebackground=bg_color,
				activeforeground=close_color,
				font=(FONT_FAMILY, FONT_SIZE),
				cursor="hand2"
			).place(relx=1.0, x=-8, y=4, anchor="ne")

			tk.Label(
				frame,
				text=title,
				fg=fg_color,
				bg=bg_color,
				font=(FONT_FAMILY, FONT_SIZE, "bold"),
				anchor="w"
			).pack(anchor="w")

			tk.Label(
				frame,
				text=message,
				fg=fg_color,
				bg=bg_color,
				font=(FONT_FAMILY, FONT_SIZE),
				anchor="w",
				justify="left",
				wraplength=(width - 20)
			).pack(anchor="w", pady=(4, 0))

			toast_root.after(timeout, toast.destroy)
			toast_root.mainloop()

		threading.Thread(target=show_toast, daemon=True).start()
		
class AIClipboardApp:
	def __init__(self, root, theme):
		self.root = root
		self.config = load_config()
		self.last_clipboard = ''
		self.tray_icon = None
		self.models_cache = {}
		self.processing = False
		self.load_models_cache()
		self.setup_ui()
		self.root.withdraw()
		self.setup_tray()
		self.start_clipboard_monitor()
		self.theme = theme

	def setup_ui(self):
		self.root.title(f"AI Clipboard – v{VERSION}")
		self.root.minsize(500, 500)
		self.root.resizable(False, False)
		self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
		self.set_icon(self.root)

		frame = ttk.Frame(self.root, padding=10)
		frame.pack(fill='both', expand=True)
		self.vars = {}
		
		font = (FONT_FAMILY, FONT_SIZE)
		font_bold = (FONT_FAMILY, FONT_SIZE, "bold")

		row_frame = tk.Frame(frame)
		row_frame.pack(fill='x', pady=(0, 5))

		left_col = tk.Frame(row_frame)
		left_col.pack(side='left', expand=True, fill='x', padx=(0, 10))

		right_col = tk.Frame(row_frame)
		right_col.pack(side='left', expand=True, fill='x')

		fields = [
			("base_url", "OpenRouter Base URL"),
			("api_key", "OpenRouter API Key"),
			("prefix", "Clipboard Prefix"),
			("clipboard_refresh_interval", "Clipboard Refresh Interval (ms)")
		]

		for i, (key, label) in enumerate(fields):
			col = left_col if i < 2 else right_col
			ttk.Label(col, text=label, font=font).pack(anchor='w', pady=(0, 5))
			
			if key == "clipboard_refresh_interval":
				self.vars[key] = tk.StringVar(value=str(self.config.get(key, 500)))
				entry = tk.Entry(col, textvariable=self.vars[key], font=font)
				entry.config(validate="key", validatecommand=(self.root.register(lambda v: v.isdigit() or v == ""), '%P'))
			elif key == "api_key":
				self.vars[key] = tk.StringVar(value=self.config.get(key, ''))
				entry = tk.Entry(col, textvariable=self.vars[key], show="*", width=25, font=font)
			else:
				self.vars[key] = tk.StringVar(value=self.config.get(key, ''))
				entry = tk.Entry(col, textvariable=self.vars[key], width=25, font=font)

			entry.pack(fill='x', pady=(0, 5))

		# Default model dropdown
		ttk.Label(frame, text="Default Model", font=font).pack(anchor='w', pady=(5, 5))
		self.default_model_var = tk.StringVar(value=self.config.get("default_model"))
		self.default_model_dropdown = ttk.Combobox(frame, textvariable=self.default_model_var,
		                                           values=self.get_model_list(), width=60, state="readonly", font=font_bold)
		self.default_model_dropdown.pack(fill='x')
		root.option_add('*TCombobox*Listbox.font', font)


		# Custom system prompt
		ttk.Label(frame, text="System Instruction (optional)", font=font).pack(anchor='w', pady=(15, 5))

		self.use_custom_prompt_var = tk.BooleanVar(value=self.config.get("use_custom_prompt", False))
		self.custom_prompt_var = tk.StringVar(value=self.config.get("custom_system_instruction", ""))

		self.custom_prompt_box = tk.Text(frame, height=5, wrap='word', font=font)
		self.custom_prompt_box.insert('1.0', self.custom_prompt_var.get())
		self.custom_prompt_box.pack(fill='x', expand=True)
		self.custom_prompt_box.config(state=tk.NORMAL if self.use_custom_prompt_var.get() else tk.DISABLED)

		def toggle_prompt_state(*_):
			self.custom_prompt_box.config(state=tk.NORMAL if self.use_custom_prompt_var.get() else tk.DISABLED)

		self.use_custom_prompt_var.trace_add("write", toggle_prompt_state)

		style = ttk.Style()
		style.configure("Custom.TCheckbutton", font=font)
		prompt_toggle = ttk.Checkbutton(frame, text="Use custom system instruction", variable=self.use_custom_prompt_var, style="Custom.TCheckbutton")
		prompt_toggle.pack(anchor='w', pady=(5, 0))
		
		# Shortcut list
		ttk.Label(frame, text="Model Shortcuts", font=font).pack(anchor='w', pady=(15, 5))
		self.shortcut_list = tk.Listbox(frame, height=5, font=font)
		self.shortcut_list.pack(fill='x')
		self.shortcut_list.bind("<Double-Button-1>", lambda e: self.edit_selected_shortcut())
		self.refresh_shortcut_list()

		btns = ttk.Frame(frame)
		btns.pack(fill='x', pady=(5, 0))
		tk.Button(btns, text="Add", padx=12, pady=2, command=self.add_shortcut, font=font).pack(side='left', padx=(0, 5))
		tk.Button(btns, text="Edit", padx=12, pady=2, command=self.edit_selected_shortcut, font=font).pack(side='left', padx=(0, 5))
		tk.Button(btns, text="Remove", padx=12, pady=2, command=self.remove_selected_shortcut, font=font).pack(side='left', padx=(0, 0))

		ttk.Label(frame, text="OpenRouter Models Cache Info", font=font).pack(anchor='w', pady=(15, 0))

		row = tk.Frame(frame)
		row.pack(fill='x', pady=(5, 0))

		self.model_cache_var = tk.StringVar(value=self.get_cache_info())
		ttk.Label(row, textvariable=self.model_cache_var, foreground="gray", font=font).pack(
			side='left', fill='x', expand=True, anchor='w'
		)

		tk.Button(row, text="Load Available Models", padx=12, pady=2, command=self.get_models, font=font).pack(
			side='right'
		)

		# Balance
		ttk.Label(frame, text="Used Balance", font=font).pack(anchor='w', pady=(10, 0))
		self.balance_var = tk.StringVar(value=f"$ {self.config.get('balance_usd', 0.0):.4f}")
		bal_frame = tk.Frame(frame)
		bal_frame.pack(fill='x', pady=(5, 0))
		tk.Label(bal_frame, textvariable=self.balance_var, font=font_bold, anchor='w', justify='left').pack(
			side='left', padx=(0, 15)
		)

		tk.Button(bal_frame, text="Reset Counter", padx=12, pady=2, command=self.reset_balance, font=font).pack(
			side='right'
		)

		ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=(25, 10))

		btn_frame = ttk.Frame(frame)
		btn_frame.pack(fill='x', pady=(5, 0))
		tk.Button(btn_frame, text="Apply", padx=12, pady=2, command=self.apply_config, font=font_bold).pack(side='right', padx=(5, 0))
		tk.Button(btn_frame, text="Cancel", padx=12, pady=2, command=self.hide_to_tray, font=font_bold).pack(side='right', padx=(5, 0))
		save_button = tk.Button(btn_frame, text="Save & Hide", padx=12, pady=2, command=self.save_and_hide, font=font_bold)
		save_button.config(default='active')
		save_button.pack(side='right')
		tk.Button(btn_frame, text="Exit", padx=12, pady=2, command=lambda: self.root.after(0, self.exit_app), font=font_bold).pack(side='left', padx=(0, 5))
		tk.Button(btn_frame, text="Help", padx=12, pady=2, command=self.show_help, font=font_bold).pack(side='left', padx=(0, 5))

		self.center_window(self.root)

	def show_help(self):
		prefix = self.vars["prefix"].get().strip()
		help = f"""How does it work?
		
Copy any text to the clipboard starting with the prefix "{prefix}" – the AI will process it and instantly return a response back to your clipboard.

Usage examples:

{prefix}prompt
- Send "prompt" to default model

{prefix}model:prompt
- Send "prompt" to model using shortcut name "model"

{prefix}@knowledge:prompt
- Send "prompt" to default model including context file "knowledge.md"

{prefix}model:@knowledge:prompt
- Send "prompt" to model using shortcut name "model", including context file "knowledge.md"

{prefix}@knowledge:model:prompt
- Send "prompt" to model using shortcut name "model", including context file "knowledge.md"
"""
		messagebox.showinfo("Help", help)
		

	def refresh_shortcut_list(self):
		self.shortcut_list.delete(0, tk.END)
		for k, v in self.config.get("model_shortcuts", {}).items():
			self.shortcut_list.insert(tk.END, f"{k}: {v}")

	def add_shortcut(self):
		popup = tk.Toplevel(self.root, padx=15, pady=15)
		popup.title("AI Clipboard – Add Shortcut")
		popup.transient(self.root)
		popup.grab_set()
		popup.resizable(False, False)
		self.set_icon(popup)
		self.center_window(popup, relative_to=self.root)

		font = (FONT_FAMILY, FONT_SIZE)
		font_bold = (FONT_FAMILY, FONT_SIZE, "bold")
		
		tk.Label(popup, text="Shortcut (a-z0-9.-_)", font=font).pack(anchor='w', pady=(0, 5))
		key_var = tk.StringVar()
		tk.Entry(popup, textvariable=key_var, font=font).pack(anchor='w', fill='x', expand=True, pady=(0, 5))

		tk.Label(popup, text="Select Model", font=font).pack(anchor='w', pady=(0, 5))
		model_var = tk.StringVar()
		model_box = ttk.Combobox(popup, textvariable=model_var, values=self.get_model_list(), width=60, state="readonly")
		model_box.pack(pady=(0, 5))

		def confirm():
			key = key_var.get().strip()
			model = model_var.get().strip()
			if not re.match(r'^[a-z0-9._-]+$', key):
				messagebox.showerror("Invalid Shortcut", "Shortcut must contain only lowercase letters, numbers, ., -, _")
				return
			if key in self.config["model_shortcuts"]:
				messagebox.showerror("Exists", "Shortcut already exists.")
				return
			if not model:
				messagebox.showerror("No Model", "You must choose a model.")
				return
			self.config["model_shortcuts"][key] = model
			popup.destroy()
			self.refresh_shortcut_list()

		btn_frame = tk.Frame(popup)
		btn_frame.pack(anchor='w', fill='x', pady=10)

		save_button = tk.Button(btn_frame, text="Save", padx=12, pady=2, command=confirm, font=font_bold)
		save_button.config(default='active')
		save_button.pack(side='right', pady=5)
		
		tk.Button(btn_frame, text="Cancel", padx=12, pady=2, command=popup.destroy, font=font).pack(side='right', pady=5, padx=(0, 5))
		self.center_window(popup, relative_to=self.root)

	def edit_selected_shortcut(self):
		idx = self.shortcut_list.curselection()
		if not idx:
			return
		key = self.shortcut_list.get(idx).split(':')[0]
		current_model = self.config["model_shortcuts"].get(key)

		font = (FONT_FAMILY, FONT_SIZE)
		font_bold = (FONT_FAMILY, FONT_SIZE, "bold")

		popup = tk.Toplevel(self.root, padx=15, pady=15)
		popup.title(f"AI Clipboard – Edit Shortcut: {key}")
		popup.transient(self.root)
		popup.grab_set()
		popup.resizable(False, False)
		self.set_icon(popup)
		self.center_window(popup, relative_to=self.root)

		tk.Label(popup, text=f"Shortcut: {key}", font=font).pack(anchor='w', pady=(0, 5))
		tk.Label(popup, text="Select New Model", font=font).pack(anchor='w', pady=(0, 5))

		model_var = tk.StringVar(value=current_model)
		model_box = ttk.Combobox(popup, textvariable=model_var, values=self.get_model_list(), width=60, state="readonly", font=font)
		model_box.pack(anchor='w', pady=(0, 5))

		def confirm():
			new_model = model_var.get().strip()
			if not new_model:
				messagebox.showerror("No Model", "You must choose a model.")
				return
			self.config["model_shortcuts"][key] = new_model
			self.refresh_shortcut_list()
			popup.destroy()


		btn_frame = tk.Frame(popup)
		btn_frame.pack(fill='x', pady=10)

		save_button = tk.Button(btn_frame, text="Save", padx=12, pady=2, command=confirm, font=font_bold)
		save_button.config(default='active')
		save_button.pack(side='right', pady=5)

		tk.Button(btn_frame, text="Cancel", padx=12, pady=2, command=popup.destroy, font=font).pack(side='right', pady=5, padx=(0, 5))

		self.center_window(popup, relative_to=self.root)
	
	def remove_selected_shortcut(self):
		idx = self.shortcut_list.curselection()
		if not idx:
			return
		key = self.shortcut_list.get(idx).split(':')[0]
		if messagebox.askyesno("Confirm", f"Remove shortcut '{key}'?"):
			del self.config["model_shortcuts"][key]
			self.refresh_shortcut_list()

	def get_model_list(self):
		if not self.models_cache:
			return []
		return sorted([m['id'] for m in self.models_cache.get('data', []) if 'id' in m])

	def reset_balance(self):
		if messagebox.askyesno("Reset Balance", "Are you sure you want to reset balance counter?"):
			self.config["balance_usd"] = 0.0
			self.balance_var.set("0.0000")
			save_config(self.config)

	def save_and_hide(self, hide = True):
		prefix = self.vars["prefix"].get().strip()
		if not prefix:
			messagebox.showerror("Invalid Prefix", "Prefix cannot be empty.")
			return

		for key in self.vars:
			value = self.vars[key].get()
			if key == "clipboard_refresh_interval":
				try:
					interval = max(100, int(value))  # Minimum 100ms
					self.config[key] = interval
					self.vars[key].set(str(interval))  # Update entry box if needed
				except ValueError:
					messagebox.showerror("Invalid Interval", "Clipboard refresh interval must be a number.")
					return
			else:
				self.config[key] = value
		
		self.config["default_model"] = self.default_model_var.get()

		use_custom = self.use_custom_prompt_var.get()
		custom_text = self.custom_prompt_box.get("1.0", "end").strip()

		if use_custom and not custom_text:
			messagebox.showerror("Empty Prompt", "Custom system instruction cannot be empty when enabled.")
			return

		self.config["use_custom_prompt"] = use_custom
		self.config["custom_system_instruction"] = custom_text
		
		save_config(self.config)
		if hide == True:
			self.hide_to_tray()

	def apply_config(self):
		self.save_and_hide(False)

	def set_icon(self, window):
		try:
			if os.path.exists(os.path.join("icons", "icon.ico")):
				window.iconbitmap(os.path.join("icons", "icon.ico"))
		except Exception as e:
			logging.warning(f"Icon load failed: {e}")

	def center_window(self, win, relative_to=None):
		win.update_idletasks()
		width = win.winfo_width()
		height = win.winfo_height()
		if relative_to:
			relative_to.update_idletasks()
			x = relative_to.winfo_rootx() + (relative_to.winfo_width() // 2) - (width // 2)
			y = relative_to.winfo_rooty() + (relative_to.winfo_height() // 2) - (height // 2)
		else:
			x = (win.winfo_screenwidth() // 2) - (width // 2)
			y = (win.winfo_screenheight() // 2) - (height // 2)
		win.geometry(f"+{x}+{y}")

	def show_main_window(self):
		self.root.deiconify()
		self.center_window(self.root)

	def hide_to_tray(self):
		self.root.withdraw()

	def setup_tray(self):
		icon_path = os.path.join("icons", "icon.ico") if os.path.exists(os.path.join("icons", "icon.ico")) else None
		image = Image.open(icon_path) if icon_path else Image.new("RGB", (64, 64), color=(0, 0, 0))
		menu = (
			item("Configuration", lambda: self.root.after(0, self.show_main_window)),
			Menu.SEPARATOR,
			item("Exit", lambda: self.root.after(0, self.exit_app))
		)
		self.tray_icon = pystray.Icon("AI Clipboard", image, "AI Clipboard", menu)
		threading.Thread(target=self.tray_icon.run, daemon=True).start()
		
	def exit_app(self):
		if messagebox.askyesno("Exit Application", "Are you sure you want to exit?"):
			if self.tray_icon:
				self.tray_icon.stop()
			self.root.destroy()

	def start_clipboard_monitor(self):
		self.check_clipboard()

	def check_clipboard(self):
		if self.processing:
			self.root.after(self.config.get("clipboard_refresh_interval", 500), self.check_clipboard)
			return
		try:
			text = pyperclip.paste().lstrip()
			if text == self.last_clipboard:
				self.root.after(self.config.get("clipboard_refresh_interval", 500), self.check_clipboard)
				return
				
			self.last_clipboard = text
			detected = self.parse_clipboard(text)
			if detected:
				model, prompt, context_key = detected
				
				context_text = ""
				
				if context_key:
					try:
						with open(os.path.join("knowledge", f"{context_key}.md"), "r", encoding="utf-8") as f:
							context_text = "\n\n" + f.read().strip()
					except FileNotFoundError:
						logging.warning(f"Knowledge file not found: {context_key}.md")
						self.notify(f"⚠️ Knowledge file not found: {context_key}.md", self.theme)
						winsound.PlaySound(os.path.join("sounds", "error.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
						self.root.after(self.config.get("clipboard_refresh_interval", 500), self.check_clipboard)
						return

				msg = f"🌐 Processing with model: {model}"
				if context_key:
					msg += f" \n📄 Knowledge file: {context_key}.md"

				self.notify(msg, theme)
				winsound.PlaySound(os.path.join("sounds", "info.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
				threading.Thread(target=self.process_prompt, args=(model, prompt, context_text), daemon=True).start()
				
		except Exception as e:
			logging.error(f"Clipboard check failed: {e}")
		self.root.after(self.config.get("clipboard_refresh_interval", 500), self.check_clipboard)

	
	def parse_clipboard(self, text):
		# Validate prefix
		if not text.lower().startswith(self.config.get("prefix", "AI:").lower()):
			return None

		# Clean and split by colon
		cleaned = text[len(self.config["prefix"]):].strip()
		parts = [p.strip() for p in cleaned.split(":") if p.strip()]

		shortcut = None
		context_key = None
		prompt_parts = []

		# Parse parts: 1 shortcut, 1 context (@), then rest as prompt
		for part in parts:
			if part.startswith("@") and context_key is None:
				context_key = part[1:].lower()
			elif shortcut is None and not part.startswith("@") and part in self.config.get("model_shortcuts", {}):
				shortcut = part.lower()
			else:
				prompt_parts.append(part)

		prompt = ":".join(prompt_parts).strip()
		if not prompt:
			return None

		model = self.config.get("default_model")
		if shortcut:
			model = self.config.get("model_shortcuts", {}).get(shortcut, model)

		return model, prompt, context_key


	def notify(self, message, theme):
		self.toast = ToastNotifier(theme=theme, root=self.root)
		self.toast.notify("AI Clipboard", message)

	def process_prompt(self, model, prompt, context_text):
		self.processing = True

		try:
			headers = {
				"Authorization": f"Bearer {self.config.get('api_key')}",
				"Content-Type": "application/json",
				"HTTP-Referer": "https://github.com/",
				"X-Title": "AI Clipboard"
			}

			if self.config.get("use_custom_prompt") and self.config.get("custom_system_instruction", "").strip():
				system_instruction = f"{self.config['custom_system_instruction'].strip()}\n\nIMPORTANT: Use text below as your context:\n{context_text}"
			else:
				system_instruction = f"""You are a direct response AI assistant. Follow these rules strictly:
1. Provide ONLY the direct answer/solution - no introductions, disclaimers, or conclusions
2. For code requests, provide ONLY the code with minimal necessary comments
3. Never ask questions back
4. Never add explanations unless explicitly requested
5. Never add pleasantries or signatures
6. Keep responses concise and to the point

IMPORTANT: Use text below as your context:
{context_text}
"""

			data = {
				"model": model,
				"messages": [
					{"role": "system", "content": system_instruction},
					{"role": "user", "content": prompt}
				],
				"temperature": 0.7
			}

			url = self.config.get("base_url").rstrip("/") + "/chat/completions"
			response = requests.post(url, headers=headers, json=data, timeout=30)
			response.raise_for_status()
			result = response.json()["choices"][0]["message"]["content"].strip()

			# Remove wrapping backticks or triple-backtick code blocks
			if result.startswith("```") and result.endswith("```"):
				result = result.split("\n", 1)[-1].rsplit("\n", 1)[0].strip()
			elif result.startswith("`") and result.endswith("`"):
				result = result[1:-1].strip()			
			
			pyperclip.copy(result)
			self.update_balance(response)
			self.notify(f"✅ Response copied to clipboard.", self.theme)
			winsound.PlaySound(os.path.join("sounds", "done.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
		except Exception as e:
			logging.error(f"Failed to process prompt: {e}")
			self.notify("❌ AI request failed.", self.theme)
			winsound.PlaySound(os.path.join("sounds", "error.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
		finally:
			self.processing = False

	def update_balance(self, response):
		try:
			usage = response.json().get("usage", {})
			prompt_tokens = usage.get("prompt_tokens", 0)
			completion_tokens = usage.get("completion_tokens", 0)
			model_id = response.json().get("model", "")

			model_info = None
			for m in self.models_cache.get("data", []):
				if m.get("id") == model_id:
					model_info = m
					break

			if model_info:
				pricing = model_info.get("pricing", {})
				prompt_price = float(pricing.get("prompt", 0))
				completion_price = float(pricing.get("completion", 0))
				total_cost = prompt_tokens * prompt_price + completion_tokens * completion_price
			else:
				# fallback if model not found in cache or missing pricing
				total_tokens = usage.get("total_tokens", 0)
				total_cost = total_tokens / 1000.0 * 0.001

			self.config["balance_usd"] = round(self.config.get("balance_usd", 0.0) + total_cost, 4)
			self.balance_var.set(f"$ {self.config['balance_usd']:.4f}")
			save_config(self.config)
		except Exception as e:
			logging.warning(f"Balance update failed: {e}")

	def get_cache_info(self):
		locale.setlocale(locale.LC_TIME, '')  # Use system locale
		
		if os.path.exists(os.path.join("cache", CACHE_PATH)):
			stamp = time.strftime('%c', time.localtime(os.path.getmtime(os.path.join("cache", CACHE_PATH))))
			return f"Cache loaded: {stamp}"
		return "No cache available"

	def get_models(self):
		try:
			url = self.config.get("base_url").rstrip("/") + "/models"
			headers = {"Authorization": f"Bearer {self.config.get('api_key')}"}
			response = requests.get(url, headers=headers)
			response.raise_for_status()
			self.models_cache = response.json()
			with open(os.path.join("cache", CACHE_PATH), 'w', encoding='utf-8') as f:
				json.dump(self.models_cache, f, indent=2)
			self.default_model_dropdown['values'] = self.get_model_list()
			self.model_cache_var.set(self.get_cache_info())
			self.notify("✅ Models loaded and cached.", self.theme)
			winsound.PlaySound(os.path.join("sounds", "done.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
		except Exception as e:
			logging.error(f"Failed to fetch models: {e}")
			self.notify("❌ Failed to fetch models.", self.theme)
			winsound.PlaySound(os.path.join("sounds", "error.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)

	def load_models_cache(self):
		if os.path.exists(os.path.join("cache", CACHE_PATH)):
			with open(os.path.join("cache", CACHE_PATH), 'r', encoding='utf-8') as f:
				self.models_cache = json.load(f)

if __name__ == '__main__':
	ensure_folders_exist()
	logging.basicConfig(
		level=logging.INFO,
		format='%(asctime)s - %(levelname)s - %(message)s',
		filename=os.path.join("logs", "ai_clipboard.log"),
		filemode='a'
	)
	root = tk.Tk()
	theme = darkdetect.theme().lower()
	app = AIClipboardApp(root, theme)
	sv_ttk.set_theme(theme)
	apply_theme_to_titlebar(root)
	root.mainloop()
