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
import argparse
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# --- CONSOLE HIDER (For Context Menu) ---
def hide_console():
    """Hides the terminal window instantly if launched from the Windows Context Menu."""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 0)

TM_DIR = ".TimeMachine"

# --- HELPER FUNCTIONS ---
def get_base_path():
    return os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

def load_config():
    config_path = os.path.join(get_base_path(), "config_vip.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f: return json.load(f)
        except Exception: pass
    return {
        "company_name": "FusionHex", "website_url": "https://www.fusionhex.com/",
        "app_title": "TimeMachine Premium", "version": "1.1.0",
        "about_text": "Instant local snapshots directly from your Windows context menu & CLI.",
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
            window.iconbitmap(default=icon_path)
            window.iconbitmap(icon_path)
    except Exception: pass

def get_permanent_icon(icon_name):
    appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'FusionHex_TimeMachine', 'assets')
    if not os.path.exists(appdata_dir): os.makedirs(appdata_dir)
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
    x = int((window.winfo_screenwidth() / 2) - (width / 2))
    y = int((window.winfo_screenheight() / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")

# --- AI & CLI JSON ENGINE ---
def out_json(status, action, data=None, error=None):
    out = {"status": status, "action": action}
    if data: out["data"] = data
    if error: out["error"] = error
    print(json.dumps(out, indent=2))
    os._exit(0 if status == "success" else 1)

# --- TIMEIGNORE LOGIC ---
def get_ignore_patterns(target_dir):
    patterns = []
    ignore_path = os.path.join(target_dir, ".timeignore")
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"): patterns.append(line.replace('\\', '/'))
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
# node_modules/
# build/
# dist/
# venv/
# .git/
# __pycache__/
# *.mp4
"""
        with open(ignore_path, "w") as f: f.write(content)

def get_files_to_zip(target_dir):
    patterns = get_ignore_patterns(target_dir)
    all_files = []
    for root, dirs, files in os.walk(target_dir):
        if TM_DIR in dirs: dirs.remove(TM_DIR)
        dirs_to_keep = []
        for d in dirs:
            dir_rel_path = os.path.relpath(os.path.join(root, d), target_dir)
            if not should_ignore(dir_rel_path, patterns): dirs_to_keep.append(d)
        dirs[:] = dirs_to_keep 
        if not dirs and not files and root != target_dir: all_files.append(root)
        for file in files:
            file_rel_path = os.path.relpath(os.path.join(root, file), target_dir)
            if file == ".timeignore" or not should_ignore(file_rel_path, patterns):
                all_files.append(os.path.join(root, file))
    return all_files

def is_duplicate_snapshot(target_dir, all_files, prefix="Snapshot"):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): return False
    snapshots = [f for f in os.listdir(tm_path) if f.startswith(prefix) and f.endswith(".zip")]
    if not snapshots: return False
    latest_snap = sorted(snapshots, key=lambda x: int(x.split("_")[1]) if "_" in x else 0)[-1]
    current_size = sum(os.path.getsize(f) for f in all_files if os.path.isfile(f))
    current_count = len(all_files)
    try:
        with zipfile.ZipFile(os.path.join(tm_path, latest_snap), 'r') as zipf:
            infos = zipf.infolist()
            return current_size == sum(info.file_size for info in infos) and current_count == len(infos)
    except Exception: return False

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
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Orange.Horizontal.TProgressbar", foreground=COLORS["accent"], background=COLORS["accent"])
        self.progress = ttk.Progressbar(self.top, length=300, mode='determinate', style="Orange.Horizontal.TProgressbar")
        self.progress.pack(pady=10)
        self.top.update()
    def update(self, value): self.progress['value'] = value; self.top.update()
    def close(self): self.top.destroy()

# --- CORE LOGIC ---
def get_next_index(target_dir, prefix):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): return 1
    indices = [int(f.split("_")[1]) for f in os.listdir(tm_path) if f.startswith(prefix) and f.endswith(".zip") and "_" in f]
    return max(indices) + 1 if indices else 1

def perform_zip_creation(target_dir, all_files, custom_name, prefix, use_gui, is_fav):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): 
        os.makedirs(tm_path)
        hide_folder(tm_path)

    index = get_next_index(target_dir, prefix)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_suffix = f"_{custom_name.replace(' ', '_')}" if custom_name else ""
    fav_suffix = "_FAV" if is_fav else ""
    snapshot_name = f"{prefix}_{index}_{timestamp}{name_suffix}{fav_suffix}.zip"
    snapshot_path = os.path.join(tm_path, snapshot_name)

    total_files = len(all_files)
    prog_win = ProgressWindow(f"Creating {prefix}", f"Zipping {total_files} files...") if use_gui else None

    try:
        with zipfile.ZipFile(snapshot_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if total_files > 0:
                for i, file_path in enumerate(all_files):
                    # FIX: Removed isfile() check so empty directories are correctly written to the zip!
                    zipf.write(file_path, os.path.relpath(file_path, target_dir))
                    if use_gui and i % max(1, total_files // 100) == 0: 
                        prog_win.update((i / total_files) * 100)
        
        if use_gui: prog_win.update(100); prog_win.close()
        return snapshot_name, total_files
    except Exception as e:
        if use_gui: prog_win.close()
        raise e

def cli_list(target_dir, json_mode):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path):
        if json_mode: out_json("success", "list", {"snapshots": []})
        else: print("No snapshots found.")
        return

    snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
    snapshots.sort(key=lambda x: int(x.split("_")[1]) if "_" in x else 0, reverse=True)
    
    data = []
    for s in snapshots:
        parts = s.split("_")
        snap_id = parts[1] if len(parts) > 1 and parts[1].isdigit() else "?"
        size_mb = round(os.path.getsize(os.path.join(tm_path, s)) / (1024*1024), 2)
        data.append({"id": snap_id, "filename": s, "size_mb": size_mb})

    if json_mode:
        out_json("success", "list", {"snapshots": data, "total": len(data)})
    else:
        print("\n=== FusionHex TimeMachine Snapshots ===")
        for d in data: print(f" [{d['id']}] {d['filename']} ({d['size_mb']} MB)")
        print("=======================================\n")
        print("Tip: Restore instantly using the ID (e.g., 'tm restore 2')\n")

def execute_snapshot(target_dir, custom_name="", prefix="Snapshot", json_mode=False, use_gui=True, is_fav=False, force=False):
    create_timeignore(target_dir, silent=True)
    all_files = get_files_to_zip(target_dir)

    if not force and is_duplicate_snapshot(target_dir, all_files, prefix):
        if json_mode:
            out_json("error", "snapshot_creation", error="Identical snapshot already exists.")
        elif use_gui:
            if not messagebox.askyesno("Duplicate Found", f"A {prefix} with identical files already exists. Create anyway?"): os._exit(0)
        else:
            print("Identical snapshot exists. Use -f or --force to bypass.")
            os._exit(0)

    try:
        snapshot_name, total_files = perform_zip_creation(target_dir, all_files, custom_name, prefix, use_gui, is_fav)
        if json_mode:
            out_json("success", "snapshot_created", {"filename": snapshot_name, "files_saved": total_files})
        elif use_gui and prefix != "Backup":
            messagebox.showinfo("TimeMachine", f"{prefix} Created: {snapshot_name}\nFiles Saved: {total_files}")
        elif not use_gui:
            print(f"Success! Created {snapshot_name} ({total_files} items)")
        
        if prefix != "Backup": os._exit(0)
    except Exception as e:
        if json_mode: out_json("error", "snapshot_creation", error=str(e))
        elif use_gui: messagebox.showerror("Error", f"Failed: {e}")
        else: print(f"Error: {e}")
        os._exit(1)

def execute_restore(target_dir, target_snap, json_mode=False, use_gui=True, make_backup=True):
    tm_path = os.path.join(target_dir, TM_DIR)
    
    if target_snap.isdigit():
        if not os.path.exists(tm_path):
            if json_mode: out_json("error", "restore", error="No snapshots found.")
            else: print("Error: No .TimeMachine folder found.")
            os._exit(1)
            
        snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
        matches = [f for f in snapshots if len(f.split("_")) > 1 and f.split("_")[1] == target_snap]
        if matches:
            target_snap = sorted(matches)[-1] 
        else:
            if json_mode: out_json("error", "restore", error=f"Snapshot ID '{target_snap}' not found.")
            elif use_gui: messagebox.showerror("Error", f"Snapshot ID '{target_snap}' not found.")
            else: print(f"Error: Snapshot ID '{target_snap}' not found.")
            os._exit(1)

    if not os.path.exists(os.path.join(tm_path, target_snap)):
        if json_mode: out_json("error", "restore", error=f"Snapshot '{target_snap}' not found.")
        elif use_gui: messagebox.showerror("Error", "Snapshot not found.")
        else: print(f"Error: Snapshot '{target_snap}' not found.")
        os._exit(1)

    if make_backup: execute_snapshot(target_dir, prefix="Backup", json_mode=False, use_gui=use_gui, is_fav=False, force=True)

    prog_win = ProgressWindow("Restoring", f"Restoring {target_snap}...") if use_gui else None
    try:
        items = [i for i in os.listdir(target_dir) if i != TM_DIR]
        for i, item in enumerate(items):
            path = os.path.join(target_dir, item)
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.unlink(path)
            if use_gui and len(items) > 0: prog_win.update((i / len(items)) * 50) 
            
        with zipfile.ZipFile(os.path.join(tm_path, target_snap), 'r') as zipf:
            members = zipf.infolist()
            for i, member in enumerate(members):
                zipf.extract(member, target_dir)
                if use_gui and len(members) > 0: prog_win.update(50 + ((i / len(members)) * 50)) 

        if use_gui: prog_win.close()
        
        if json_mode: out_json("success", "restored", {"restored_from": target_snap})
        elif use_gui: messagebox.showinfo("Success", f"Folder Restored perfectly from {target_snap}!")
        else: print(f"Successfully restored from {target_snap}")
        os._exit(0) 
    except Exception as e:
        if use_gui: prog_win.close(); messagebox.showerror("Error", f"Restore Error: {e}")
        elif json_mode: out_json("error", "restore", error=str(e))
        else: print(f"Error: {e}")
        os._exit(1)

# --- INSTALLER GUI ---
class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{CONFIG['company_name']} - {CONFIG['app_title']}")
        center_window(self.root, 500, 380)
        self.root.configure(bg=COLORS["bg"])
        self.exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        set_window_icon(self.root)

        tk.Label(root, text=CONFIG['app_title'], font=("Segoe UI", 20, "bold"), bg=COLORS["bg"], fg=COLORS["primary"]).pack(pady=(20, 0))
        tk.Label(root, text=f"v{CONFIG['version']} by {CONFIG['company_name']}", font=("Segoe UI", 10), bg=COLORS["bg"], fg=COLORS["accent"]).pack()
        tk.Label(root, text=CONFIG['about_text'], font=("Segoe UI", 9), bg=COLORS["bg"], fg="#aaaaaa", wraplength=400, justify="center").pack(pady=15)

        btn_frame = tk.Frame(root, bg=COLORS["bg"])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Install Context Menu & CLI", font=("Segoe UI", 10, "bold"), bg=COLORS["primary"], fg="white", relief="flat", width=35, pady=8, command=lambda: threading.Thread(target=self.install_reg, daemon=True).start()).pack(pady=5)
        tk.Button(btn_frame, text="Remove Menu", font=("Segoe UI", 10, "bold"), bg=COLORS["danger"], fg="white", relief="flat", width=35, pady=8, command=lambda: threading.Thread(target=self.uninstall_reg, daemon=True).start()).pack(pady=5)

    def add_to_path(self, appdata_dir):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            try: path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError: path = ""
            
            if appdata_dir.lower() not in path.lower():
                new_path = f"{path};{appdata_dir}" if path else appdata_dir
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                HWND_BROADCAST = 0xFFFF; WM_SETTINGCHANGE = 0x001A; SMTO_ABORTIFHUNG = 0x0002
                ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(ctypes.c_ulong()))
            winreg.CloseKey(key)
        except Exception as e: print(f"Path Error: {e}")

    def get_permanent_exe(self):
        appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'FusionHex_TimeMachine')
        if not os.path.exists(appdata_dir): os.makedirs(appdata_dir)
            
        perm_exe = os.path.join(appdata_dir, "tm.exe")
        perm_config = os.path.join(appdata_dir, "config_vip.json")
        
        self.add_to_path(appdata_dir) 
        
        if self.exe_path.lower() != perm_exe.lower():
            try: 
                shutil.copy2(self.exe_path, perm_exe)
                local_config = os.path.join(get_base_path(), "config_vip.json")
                if os.path.exists(local_config): shutil.copy2(local_config, perm_config)
            except Exception: pass
        return perm_exe if os.path.exists(perm_exe) else self.exe_path

    def install_reg(self):
        prog = ProgressWindow("Installing", "Writing to Windows Registry...")
        safe_exe = self.get_permanent_exe().replace("\\", "\\\\")
        icon_main = get_permanent_icon("app_icon.ico").replace("\\", "\\\\")
        icon_create = get_permanent_icon("create.ico").replace("\\", "\\\\")
        icon_fav = get_permanent_icon("fav.ico").replace("\\", "\\\\")
        icon_restore = get_permanent_icon("restore.ico").replace("\\", "\\\\")

        reg_content = f"""Windows Registry Editor Version 5.00
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine]
"MUIVerb"="{CONFIG['app_title']}"
"SubCommands"=""
"Icon"="\\"{icon_main}\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\01create]
@="Create Snapshot"
"Icon"="\\"{icon_create}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\01create\\command]
@="\\"{safe_exe}\\" _ctx_create \\"%V\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\02fav]
@="Create Favorite Snapshot"
"Icon"="\\"{icon_fav}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\02fav\\command]
@="\\"{safe_exe}\\" _ctx_create \\"%V\\" --fav"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\03restore]
@="Restore from Snapshot..."
"CommandFlags"=dword:00000020
"Icon"="\\"{icon_restore}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine\\shell\\03restore\\command]
@="\\"{safe_exe}\\" _ctx_restore \\"%V\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine]
"MUIVerb"="{CONFIG['app_title']}"
"SubCommands"=""
"Icon"="\\"{icon_main}\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\01create]
@="Create Snapshot"
"Icon"="\\"{icon_create}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\01create\\command]
@="\\"{safe_exe}\\" _ctx_create \\"%1\\""

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\02fav]
@="Create Favorite Snapshot"
"Icon"="\\"{icon_fav}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\02fav\\command]
@="\\"{safe_exe}\\" _ctx_create \\"%1\\" --fav"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\03restore]
@="Restore from Snapshot..."
"CommandFlags"=dword:00000020
"Icon"="\\"{icon_restore}\\""
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine\\shell\\03restore\\command]
@="\\"{safe_exe}\\" _ctx_restore \\"%1\\""
"""
        reg_file = os.path.abspath("install_tm.reg")
        with open(reg_file, "w") as f: f.write(reg_content)
        import time; time.sleep(1); prog.update(50)
        subprocess.run(['reg.exe', 'import', reg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(reg_file): os.remove(reg_file)
        prog.update(100); time.sleep(0.5); prog.close()
        messagebox.showinfo("Success", "Context Menu & CLI Installed!\n\nYou can now type 'tm commands' in any terminal.")

    def uninstall_reg(self):
        prog = ProgressWindow("Removing", "Scrubbing Registry Keys...")
        reg_file = os.path.abspath("uninstall_tm.reg")
        with open(reg_file, "w") as f: f.write("Windows Registry Editor Version 5.00\n[-HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\TimeMachine]\n[-HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\TimeMachine]\n")
        import time; time.sleep(1); prog.update(50)
        subprocess.run(['reg.exe', 'import', reg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(reg_file): os.remove(reg_file)
        prog.update(100); time.sleep(0.5); prog.close()
        messagebox.showinfo("Success", "Registry scrubbed cleanly!")

# --- ENTRY POINT & CLI PARSER ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="tm", description="FusionHex TimeMachine CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Internal Context Menu Commands
    p_ctx_create = subparsers.add_parser("_ctx_create")
    p_ctx_create.add_argument("path")
    p_ctx_create.add_argument("--fav", action="store_true")
    
    p_ctx_restore = subparsers.add_parser("_ctx_restore")
    p_ctx_restore.add_argument("path")

    # Public CLI Commands
    p_snap = subparsers.add_parser("snapshot", help="Create a snapshot")
    p_snap.add_argument("name", nargs="?", default="", help="Optional name suffix")
    p_snap.add_argument("--fav", action="store_true", help="Mark as favorite")
    p_snap.add_argument("-f", "--force", action="store_true", help="Force create even if identical")
    p_snap.add_argument("--json", action="store_true", help="Output pure JSON")

    p_list = subparsers.add_parser("list", help="List snapshots")
    p_list.add_argument("--json", action="store_true", help="Output pure JSON")

    p_ignore = subparsers.add_parser("ignore", help="Add pattern to .timeignore")
    p_ignore.add_argument("pattern", help="Folder or file pattern (e.g. node_modules/)")
    p_ignore.add_argument("--json", action="store_true", help="Output pure JSON")

    p_restore = subparsers.add_parser("restore", help="Restore a snapshot")
    p_restore.add_argument("id_or_name", help="Exact filename or ID of the snapshot to restore")
    p_restore.add_argument("--json", action="store_true", help="Output pure JSON")
    
    # New Commands Menu
    p_cmds = subparsers.add_parser("commands", help="Show all available CLI commands")
    p_help = subparsers.add_parser("help", help="Show all available CLI commands")

    args = parser.parse_args()

    # GUI Mode (No arguments)
    if not args.command:
        root = tk.Tk(); center_window(root, 0, 0); set_window_icon(root)
        InstallerGUI(root)
        root.mainloop()

    # Context Menu Mode (Hide Console, Show GUI)
    elif args.command in ["_ctx_create", "_ctx_restore"]:
        hide_console() 
        root = tk.Tk(); root.withdraw(); set_window_icon(root)
        target = args.path.strip('"') if args.path else os.getcwd()
        
        if args.command == "_ctx_create":
            threading.Thread(target=execute_snapshot, args=(target, "", "Snapshot", False, True, args.fav, False), daemon=True).start()
            root.mainloop()
        elif args.command == "_ctx_restore":
            tm_path = os.path.join(target, TM_DIR)
            if not os.path.exists(tm_path): messagebox.showerror("Error", "No snapshots here."); os._exit(0)
            
            snapshots = sorted([f for f in os.listdir(tm_path) if f.endswith(".zip")], reverse=True)
            top = tk.Toplevel(); top.title("Restore"); center_window(top, 380, 420); top.configure(bg=COLORS["bg"]); set_window_icon(top)
            top.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
            tk.Label(top, text="Select Snapshot", bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI", 12, "bold")).pack(pady=10)
            lb = tk.Listbox(top, bg="#2d2d2d", fg=COLORS["fg"]); lb.pack(fill="both", expand=True, padx=20)
            for s in snapshots: lb.insert(tk.END, s)
            def on_sel():
                ch = lb.get(tk.ACTIVE)
                if ch and messagebox.askyesno("Confirm", f"Restore {ch}?"):
                    top.destroy()
                    threading.Thread(target=execute_restore, args=(target, ch, False, True, True), daemon=True).start()
                else: os._exit(0)
            tk.Button(top, text="RESTORE", bg=COLORS["danger"], fg=COLORS["fg"], command=on_sel).pack(pady=15, fill="x", padx=20)
            root.mainloop()

    # CLI / AI Mode (Stay in terminal)
    else:
        cwd = os.getcwd()
        if args.command in ["commands", "help"]:
            print("\n=== FusionHex TimeMachine CLI Commands ===")
            print(" tm snapshot [name]  : Create snapshot (Options: -f to force, --fav for favorite, --json)")
            print(" tm restore <ID>     : Restore a snapshot by its ID or filename")
            print(" tm list             : List all snapshots and their IDs")
            print(" tm ignore <pattern> : Add a file/folder to .timeignore (e.g. tm ignore node_modules/)")
            print(" tm commands         : Show this help menu")
            print("==========================================\n")
            os._exit(0)
        elif args.command == "snapshot":
            execute_snapshot(cwd, custom_name=args.name, json_mode=args.json, use_gui=False, is_fav=args.fav, force=args.force)
        elif args.command == "list":
            cli_list(cwd, json_mode=args.json)
        elif args.command == "ignore":
            with open(os.path.join(cwd, ".timeignore"), "a") as f: f.write(f"\n{args.pattern}")
            if args.json: out_json("success", "ignore_added", {"pattern": args.pattern})
            else: print(f"Added {args.pattern} to .timeignore")
        elif args.command == "restore":
            execute_restore(cwd, args.id_or_name, json_mode=args.json, use_gui=False, make_backup=True)