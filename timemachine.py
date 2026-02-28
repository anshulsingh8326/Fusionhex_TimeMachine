import os
import sys
import shutil
import zipfile
import subprocess
import ctypes
import json
import threading
import webbrowser
import fnmatch
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

TM_DIR = ".TimeMachine"

# --- HELPER FUNCTIONS ---

def get_base_path():
    return os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

def load_config():
    config_path = os.path.join(get_base_path(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "company_name": "FusionHex", "website_url": "https://www.fusionhex.com/",
        "app_title": "TimeMachine", "version": "1.0.7",
        "about_text": "Instant local snapshots directly from your Windows context menu.",
        "colors": {"bg": "#1a1a1a", "fg": "#ffffff", "primary": "#0078D7", "accent": "#ff9800", "danger": "#d32f2f"}
    }

CONFIG = load_config()
COLORS = CONFIG["colors"]

def resource_path(relative_path):
    base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else get_base_path()
    return os.path.join(base, relative_path)

def set_window_icon(window):
    try:
        icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception:
        pass

def get_permanent_icon(icon_name):
    appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'FusionHex_TimeMachine', 'assets')
    if not os.path.exists(appdata_dir):
        os.makedirs(appdata_dir)
        
    src = resource_path(os.path.join("assets", icon_name))
    dst = os.path.join(appdata_dir, icon_name)
    
    if os.path.exists(src):
        try: shutil.copy2(src, dst)
        except Exception: pass
        
    return dst if os.path.exists(dst) else ""

def hide_folder(path):
    try: ctypes.windll.kernel32.SetFileAttributesW(str(path), 2)
    except: pass

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")

# --- TIMEIGNORE LOGIC ---

def get_ignore_patterns(target_dir):
    patterns = []
    ignore_path = os.path.join(target_dir, ".timeignore")
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line.replace('\\', '/'))
    return patterns

def should_ignore(rel_path, patterns):
    rel_path = rel_path.replace('\\', '/')
    path_parts = rel_path.split('/')
    
    for pattern in patterns:
        pattern = pattern.strip('/')
        if fnmatch.fnmatch(path_parts[-1], pattern): return True
        if any(fnmatch.fnmatch(part, pattern) for part in path_parts): return True
        if fnmatch.fnmatch(rel_path, pattern): return True
            
    return False

def create_timeignore(target_dir, silent=False):
    ignore_path = os.path.join(target_dir, ".timeignore")
    if not os.path.exists(ignore_path):
        content = """# FusionHex TimeMachine Ignore File
# Add folder or file names below to exclude them from snapshots.
# Syntax supports basic wildcards (similar to .gitignore).
# Lines starting with '#' are comments and ignored. Remove the '#' to exclude folders/files. 
# 
#
# Examples:
# node_modules/
# Library/
# build/
# *.mp4
# *.exe

venv/
build/
__pycache__/
*.spec
.git/
"""
        with open(ignore_path, "w") as f:
            f.write(content)
        if not silent:
            messagebox.showinfo("Success", "Created .timeignore file. Open it to add exclusions.")

# --- PROGRESS UI (MODAL) ---

class ProgressWindow:
    def __init__(self, title, message):
        self.top = tk.Toplevel()
        self.top.title(title)
        center_window(self.top, 350, 120)
        self.top.configure(bg=COLORS["bg"])
        self.top.resizable(False, False)
        self.top.attributes("-topmost", True)
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        set_window_icon(self.top)

        tk.Label(self.top, text=message, bg=COLORS["bg"], fg=COLORS["fg"], font=("Segoe UI", 10)).pack(pady=(15, 5))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Orange.Horizontal.TProgressbar", foreground=COLORS["accent"], background=COLORS["accent"])
        
        self.progress = ttk.Progressbar(self.top, length=300, mode='determinate', style="Orange.Horizontal.TProgressbar")
        self.progress.pack(pady=10)
        self.top.update()

    def update(self, value):
        self.progress['value'] = value
        self.top.update()

    def close(self):
        self.top.destroy()

# --- CORE LOGIC (THREADED SNAPSHOTS) ---

def get_next_snapshot_index(target_dir):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): return 1
    indices = [int(f.split("_")[1]) for f in os.listdir(tm_path) if f.startswith("Snapshot_") and f.endswith(".zip") and "_" in f]
    return max(indices) + 1 if indices else 1

def create_snapshot_thread(target_dir, is_fav):
    create_timeignore(target_dir, silent=True)

    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): 
        os.makedirs(tm_path)
        hide_folder(tm_path)

    patterns = get_ignore_patterns(target_dir)
    index = get_next_snapshot_index(target_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fav_suffix = "_FAV" if is_fav else ""
    snapshot_name = f"Snapshot_{index}_{timestamp}{fav_suffix}.zip"
    snapshot_path = os.path.join(tm_path, snapshot_name)

    all_files = []
    
    for root, dirs, files in os.walk(target_dir):
        if TM_DIR in dirs: dirs.remove(TM_DIR)
            
        dirs_to_keep = []
        for d in dirs:
            dir_rel_path = os.path.relpath(os.path.join(root, d), target_dir)
            if not should_ignore(dir_rel_path, patterns):
                dirs_to_keep.append(d)
        dirs[:] = dirs_to_keep 
        
        for file in files:
            file_rel_path = os.path.relpath(os.path.join(root, file), target_dir)
            if file == ".timeignore" or not should_ignore(file_rel_path, patterns):
                all_files.append(os.path.join(root, file))

    total_files = len(all_files)
    prog_win = ProgressWindow("Creating Snapshot", f"Zipping {total_files} files...")

    try:
        with zipfile.ZipFile(snapshot_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if total_files > 0:
                for i, file_path in enumerate(all_files):
                    zipf.write(file_path, os.path.relpath(file_path, target_dir))
                    if i % max(1, total_files // 100) == 0: 
                        prog_win.update((i / total_files) * 100)
        
        prog_win.update(100)
        prog_win.close()
        messagebox.showinfo("TimeMachine", f"Snapshot Created: {snapshot_name}\nFiles Saved: {total_files}")
        os._exit(0) # INSTANTLY KILL GHOST PROCESS
    except Exception as e:
        prog_win.close()
        messagebox.showerror("Error", f"Failed: {e}")
        os._exit(1) # KILL ON ERROR

def restore_snapshot_thread(target_dir, snapshot_name):
    prog_win = ProgressWindow("Restoring Snapshot", f"Restoring from {snapshot_name}...")
    try:
        tm_path = os.path.join(target_dir, TM_DIR)
        
        items = [i for i in os.listdir(target_dir) if i != TM_DIR]
        for i, item in enumerate(items):
            path = os.path.join(target_dir, item)
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.unlink(path)
            if len(items) > 0:
                prog_win.update((i / len(items)) * 50) 
            
        zip_path = os.path.join(tm_path, snapshot_name)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            members = zipf.infolist()
            for i, member in enumerate(members):
                zipf.extract(member, target_dir)
                if len(members) > 0:
                    prog_win.update(50 + ((i / len(members)) * 50)) 

        prog_win.close()
        messagebox.showinfo("Success", "Folder Restored perfectly!")
        os._exit(0) # INSTANTLY KILL GHOST PROCESS
    except Exception as e:
        prog_win.close()
        messagebox.showerror("Error", f"Restore Error: {e}")
        os._exit(1) # KILL ON ERROR

def initiate_restore(target_dir):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.isdir(tm_path):
        messagebox.showerror("Error", "No .TimeMachine folder found here.")
        os._exit(0)

    snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
    if not snapshots:
        messagebox.showwarning("Empty", "No snapshots found.")
        os._exit(0)

    snapshots.sort(key=lambda x: int(x.split("_")[1]) if "_" in x else 0, reverse=True)

    def on_select():
        choice = listbox.get(tk.ACTIVE)
        if choice:
            top.destroy()
            if messagebox.askyesno("Confirm", "This will WIPE current files and restore. Proceed?"):
                threading.Thread(target=restore_snapshot_thread, args=(target_dir, choice), daemon=True).start()
            else:
                os._exit(0) # KILL IF USER CANCELS

    top = tk.Toplevel()
    top.title(f"{CONFIG['company_name']} Restore")
    center_window(top, 380, 420)
    top.configure(bg=COLORS["bg"])
    set_window_icon(top)
    
    # If user hits the 'X' to close the window, kill the process
    top.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    
    tk.Label(top, text="Select Snapshot to Restore", bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI", 12, "bold")).pack(pady=(15,5))
    listbox = tk.Listbox(top, bg="#2d2d2d", fg=COLORS["fg"], selectbackground=COLORS["primary"], relief="flat", font=("Consolas", 10))
    listbox.pack(fill="both", expand=True, padx=20, pady=5)
    for s in snapshots: listbox.insert(tk.END, s)
    
    tk.Button(top, text="RESTORE SELECTED", bg=COLORS["danger"], fg=COLORS["fg"], font=("Segoe UI", 10, "bold"), relief="flat", command=on_select).pack(pady=15, fill="x", padx=20)

# --- INSTALLER GUI ---

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{CONFIG['company_name']} - {CONFIG['app_title']} Setup")
        center_window(self.root, 500, 380)
        self.root.configure(bg=COLORS["bg"])
        self.exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        set_window_icon(self.root)

        tk.Label(root, text=CONFIG['app_title'], font=("Segoe UI", 20, "bold"), bg=COLORS["bg"], fg=COLORS["primary"]).pack(pady=(20, 0))
        tk.Label(root, text=f"v{CONFIG['version']} by {CONFIG['company_name']}", font=("Segoe UI", 10), bg=COLORS["bg"], fg=COLORS["accent"]).pack()
        tk.Label(root, text=CONFIG['about_text'], font=("Segoe UI", 9), bg=COLORS["bg"], fg="#aaaaaa", wraplength=400, justify="center").pack(pady=15)

        btn_frame = tk.Frame(root, bg=COLORS["bg"])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Install Context Menu", font=("Segoe UI", 10, "bold"), bg=COLORS["primary"], fg="white", relief="flat", width=35, pady=8, command=lambda: self.run_threaded(self.install_reg)).pack(pady=5)
        tk.Button(btn_frame, text="Remove Menu", font=("Segoe UI", 10, "bold"), bg=COLORS["danger"], fg="white", relief="flat", width=35, pady=8, command=lambda: self.run_threaded(self.uninstall_reg)).pack(pady=5)

        link = tk.Label(root, text=CONFIG['website_url'], font=("Segoe UI", 9, "underline"), bg=COLORS["bg"], fg=COLORS["accent"], cursor="hand2")
        link.pack(side="bottom", pady=15)
        link.bind("<Button-1>", lambda e: webbrowser.open_new(CONFIG['website_url']))

    def run_threaded(self, func):
        threading.Thread(target=func, daemon=True).start()
        
    def get_permanent_exe(self):
        """Copies the EXE and config.json to a permanent AppData folder."""
        appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'FusionHex_TimeMachine')
        if not os.path.exists(appdata_dir):
            os.makedirs(appdata_dir)
            
        perm_exe = os.path.join(appdata_dir, "TimeMachine.exe")
        perm_config = os.path.join(appdata_dir, "config.json")
        
        # Don't copy if we are already running from AppData
        if self.exe_path.lower() != perm_exe.lower():
            try: 
                # Copy the EXE
                shutil.copy2(self.exe_path, perm_exe)
                
                # Copy the config.json file alongside it!
                local_config = os.path.join(get_base_path(), "config.json")
                if os.path.exists(local_config):
                    shutil.copy2(local_config, perm_config)
            except Exception: pass
                
        return perm_exe if os.path.exists(perm_exe) else self.exe_path

    def get_reg_content(self):
        # We now map the registry to the cloned AppData EXE!
        safe_exe = self.get_permanent_exe().replace("\\", "\\\\")
        
        icon_main = get_permanent_icon("app_icon.ico").replace("\\", "\\\\")
        icon_create = get_permanent_icon("create.ico").replace("\\", "\\\\")
        icon_fav = get_permanent_icon("fav.ico").replace("\\", "\\\\")
        icon_restore = get_permanent_icon("restore.ico").replace("\\", "\\\\")

        return f"""Windows Registry Editor Version 5.00

; --- BACKGROUND MENU ---
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine]
"MUIVerb"="{CONFIG['app_title']}"
"SubCommands"=""
"Icon"="\\"{icon_main}\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\01create]
@="Create Snapshot"
"Icon"="\\"{icon_create}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\01create\\command]
@="\\"{safe_exe}\\" create \\"%V\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\02fav]
@="Create Favorite Snapshot"
"Icon"="\\"{icon_fav}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\02fav\\command]
@="\\"{safe_exe}\\" create \\"%V\\" --fav"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\03restore]
@="Restore from Snapshot..."
"CommandFlags"=dword:00000020
"Icon"="\\"{icon_restore}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\03restore\\command]
@="\\"{safe_exe}\\" restore \\"%V\\""

; --- DIRECTORY MENU (FOLDER ICON) ---
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine]
"MUIVerb"="{CONFIG['app_title']}"
"SubCommands"=""
"Icon"="\\"{icon_main}\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\01create]
@="Create Snapshot"
"Icon"="\\"{icon_create}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\01create\\command]
@="\\"{safe_exe}\\" create \\"%1\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\02fav]
@="Create Favorite Snapshot"
"Icon"="\\"{icon_fav}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\02fav\\command]
@="\\"{safe_exe}\\" create \\"%1\\" --fav"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\03restore]
@="Restore from Snapshot..."
"CommandFlags"=dword:00000020
"Icon"="\\"{icon_restore}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\03restore\\command]
@="\\"{safe_exe}\\" restore \\"%1\\""
"""

    def install_reg(self):
        prog = ProgressWindow("Installing", "Writing to Windows Registry...")
        reg_file = os.path.abspath("install_tm.reg")
        with open(reg_file, "w") as f: f.write(self.get_reg_content())
        import time; time.sleep(1)
        prog.update(50)
        subprocess.run(['reg.exe', 'import', reg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(reg_file): os.remove(reg_file)
        prog.update(100)
        time.sleep(0.5)
        prog.close()
        messagebox.showinfo("Success", "Context Menu Installed! You can safely move or delete this setup file.")

    def uninstall_reg(self):
        prog = ProgressWindow("Removing", "Scrubbing Registry Keys...")
        reg_file = os.path.abspath("uninstall_tm.reg")
        content = """Windows Registry Editor Version 5.00
[-HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine]
[-HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine]
"""
        with open(reg_file, "w") as f: f.write(content)
        import time; time.sleep(1)
        prog.update(50)
        subprocess.run(['reg.exe', 'import', reg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(reg_file): os.remove(reg_file)
        prog.update(100)
        time.sleep(0.5)
        prog.close()
        messagebox.showinfo("Success", "Registry scrubbed cleanly!")

# --- ENTRY POINT ---

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs='?', choices=["create", "restore"])
    parser.add_argument("path", nargs='?')
    parser.add_argument("--fav", action="store_true")
    args = parser.parse_args()

    if not args.command:
        root = tk.Tk()
        center_window(root, 0, 0)
        InstallerGUI(root)
        root.mainloop()
    else:
        root = tk.Tk()
        root.withdraw()
        target = args.path.strip('"') if args.path else os.getcwd()
        
        if args.command == "create":
            threading.Thread(target=create_snapshot_thread, args=(target, args.fav), daemon=True).start()
            root.mainloop()
        elif args.command == "restore":
            initiate_restore(target)
            root.mainloop()