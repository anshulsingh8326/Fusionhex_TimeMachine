import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from core import get_base_path, hide_folder, get_files_to_zip, is_duplicate_snapshot, perform_zip_creation, TM_DIR, get_tracked_folders

def load_config():
    config_path = os.path.join(get_base_path(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f: return json.load(f)
        except Exception: pass
    return {}

CONFIG = load_config()
COLORS = CONFIG.get("colors", {
    "bg": "#120e0c", "fg": "#f5f5f5", "primary": "#ff9800", "secondary": "#0288D1",
    "danger": "#d32f2f", "card": "#1e1814", "border": "#3a2e26", "primary_hover": "#ffb74d", "danger_hover": "#f44336"
})

def resource_path(relative_path):
    base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else get_base_path()
    return os.path.join(base, relative_path)

def set_window_icon(window, icon_name):
    try:
        icon_path = resource_path(os.path.join("assets", icon_name))
        if os.path.exists(icon_path):
            window.iconbitmap(default=icon_path)
            window.iconbitmap(icon_path)
    except Exception: pass

def center_window(window, width, height):
    window.update_idletasks()
    x = int((window.winfo_screenwidth() / 2) - (width / 2))
    y = int((window.winfo_screenheight() / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")

def draw_rounded_rect(canvas, x, y, w, h, c, fill, tag="bg"):
    canvas.delete(tag)
    canvas.create_oval(x, y, x+c, y+c, fill=fill, outline="", tags=tag)
    canvas.create_oval(x+w-c, y, x+w, y+c, fill=fill, outline="", tags=tag)
    canvas.create_oval(x, y+h-c, x+c, y+h, fill=fill, outline="", tags=tag)
    canvas.create_oval(x+w-c, y+h-c, x+w, y+h, fill=fill, outline="", tags=tag)
    canvas.create_rectangle(x+c/2, y, x+w-c/2, y+h, fill=fill, outline="", tags=tag)
    canvas.create_rectangle(x, y+c/2, x+w, y+h-c/2, fill=fill, outline="", tags=tag)

class ActionButton(tk.Canvas):
    def __init__(self, parent, width, height, text, bg, hover_bg, fg, command):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg"], highlightthickness=0)
        self.command = command
        self.bg_color, self.hover_bg = bg, hover_bg
        draw_rounded_rect(self, 0, 0, width, height, 16, bg, "bg")
        self.txt_id = self.create_text(width//2, height//2, text=text, fill=fg, font=("Segoe UI", 11, "bold"), anchor="center")
        self.bind("<Enter>", lambda e: self.itemconfig("bg", fill=self.hover_bg))
        self.bind("<Leave>", lambda e: self.itemconfig("bg", fill=self.bg_color))
        self.bind("<Button-1>", lambda e: self.command())
        self.tag_bind(self.txt_id, "<Button-1>", lambda e: self.command())

class AndroidToggle(tk.Canvas):
    def __init__(self, parent, command=None, initial_state=True):
        super().__init__(parent, width=50, height=28, bg=COLORS["bg"], highlightthickness=0)
        self.state = initial_state
        self.command = command
        self.bind("<Button-1>", self.toggle)
        self.update_visuals()
        
    def update_visuals(self):
        self.delete("all")
        bg_color = COLORS["primary"] if self.state else COLORS["border"]
        draw_rounded_rect(self, 2, 4, 40, 20, 20, bg_color, "track")
        thumb_x = 22 if self.state else 4
        self.create_oval(thumb_x, 6, thumb_x+16, 22, fill=COLORS["bg"], outline="")
        
    def toggle(self, e):
        self.state = not self.state
        self.update_visuals()
        if self.command: self.command(self.state)

class ItemCard(tk.Canvas):
    def __init__(self, parent, width, height, text, value, command, is_path=False):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg"], highlightthickness=0)
        self.value, self.command, self.is_selected = value, command, False
        
        display_text = f"📁   {os.path.basename(text)}" if is_path else text
        
        draw_rounded_rect(self, 2, 2, width-4, height-4, 12, COLORS["card"], "bg")
        self.txt = self.create_text(15, height//2, text=display_text, fill=COLORS["fg"], font=("Segoe UI", 11), anchor="w")
        
        if is_path:
            self.sub_txt = self.create_text(width-20, height//2, text="open \u2192", fill=COLORS["secondary"], font=("Segoe UI", 9, "italic"), anchor="e")
            self.tag_bind(self.sub_txt, "<Button-1>", lambda e: self.command(self.value))

        self.bind("<Enter>", lambda e: self.itemconfig("bg", fill=COLORS["border"]) if not self.is_selected else None)
        self.bind("<Leave>", lambda e: self.itemconfig("bg", fill=COLORS["primary"] if self.is_selected else COLORS["card"]))
        self.bind("<Button-1>", lambda e: self.command(self.value))
        self.tag_bind(self.txt, "<Button-1>", lambda e: self.command(self.value))
        
    def set_selected(self, selected):
        self.is_selected = selected
        color, text_color = (COLORS["primary"], COLORS["bg"]) if selected else (COLORS["card"], COLORS["fg"])
        self.itemconfig("bg", fill=color)
        self.itemconfig(self.txt, fill=text_color)

class ProgressWindow:
    def __init__(self, title, message):
        self.top = tk.Toplevel()
        self.top.title(title)
        center_window(self.top, 380, 140)
        self.top.configure(bg=COLORS["bg"], bd=2, relief="flat")
        self.top.resizable(False, False)
        self.top.attributes("-topmost", True)
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        
        main_frame = tk.Frame(self.top, bg=COLORS["card"], bd=1, relief="solid", highlightbackground=COLORS["border"], highlightthickness=1)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(main_frame, text=message, bg=COLORS["card"], fg=COLORS["fg"], font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Fusion.Horizontal.TProgressbar", foreground=COLORS["primary"], background=COLORS["primary"], troughcolor=COLORS["bg"], bordercolor=COLORS["border"])
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate', style="Fusion.Horizontal.TProgressbar")
        self.progress.pack(pady=(0, 20))
        self.top.update()
        
    def update(self, value): self.top.after(0, lambda: self.progress.configure(value=value))
    def close(self): self.top.after(0, self.top.destroy)

def show_home_window(root, is_vip, icon_name):
    title_str = CONFIG.get("vipapp_title", "TimeMachine VIP") if is_vip else CONFIG.get("app_title", "TimeMachine")
    version_str = CONFIG.get("version_vip", "1.1.0") if is_vip else CONFIG.get("version", "1.0.9")
    
    root.title(f"{CONFIG.get('company_name', 'FusionHex')} - {title_str}")
    center_window(root, 720, 650)
    root.configure(bg=COLORS["bg"])
    set_window_icon(root, icon_name)

    header = tk.Frame(root, bg=COLORS["bg"], pady=10)
    header.pack(fill="x", padx=15, pady=(15, 0))
    tk.Label(header, text=title_str, font=("Segoe UI", 24, "bold"), bg=COLORS["bg"], fg=COLORS["primary"]).pack()
    tk.Label(header, text=f"v{version_str} - Tracked Projects", font=("Segoe UI", 10), bg=COLORS["bg"], fg=COLORS["secondary"]).pack(pady=(2,10))

    list_frame = tk.Frame(root, bg=COLORS["bg"])
    list_frame.pack(fill="both", expand=True, padx=30, pady=5)
    
    canvas = tk.Canvas(list_frame, bg=COLORS["bg"], highlightthickness=0)
    style = ttk.Style(); style.theme_use('clam')
    style.configure("Dark.Vertical.TScrollbar", background=COLORS["border"], troughcolor=COLORS["bg"], bordercolor=COLORS["bg"], arrowcolor=COLORS["primary"], relief="flat", borderwidth=0)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
    scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])

    # This dynamically centers the inner frame within the canvas
    canvas_window = canvas.create_window((330, 0), window=scrollable_frame, anchor="n")
    
    def on_configure(e):
        canvas.itemconfig(canvas_window, width=e.width)
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    canvas.bind("<Configure>", on_configure)
    root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
    
    folders = get_tracked_folders()
    selected_folder = [None]
    cards = []
    
    def handle_card_select(val):
        selected_folder[0] = val
        for c in cards: c.set_selected(c.value == val)

    if not folders:
        tk.Label(scrollable_frame, text="No projects tracked yet.\n\nRight-click inside any folder in Windows Explorer\nand select 'Create Snapshot' to get started.", font=("Segoe UI", 10), bg=COLORS["bg"], fg="#777", justify="center").pack(pady=40)
    else:
        for f_path in folders:
            card = ItemCard(scrollable_frame, 620, 45, f_path, f_path, handle_card_select, is_path=True)
            card.pack(pady=5, anchor="center")
            cards.append(card)
    
    def do_open():
        ch = selected_folder[0]
        if ch and os.path.exists(ch): os.startfile(ch)
        elif ch: messagebox.showwarning("Missing", "Folder no longer exists.")
        else: messagebox.showwarning("Warning", "Select a project first.")

    ActionButton(root, 500, 45, "OPEN LOCATION IN EXPLORER", COLORS["primary"], COLORS["primary_hover"], COLORS["bg"], command=do_open).pack(pady=25)