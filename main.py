import os
import sys
import argparse
import threading
import shutil
import zipfile
import traceback
import ctypes
import tkinter as tk
from tkinter import messagebox, ttk
from core import get_base_path, get_files_to_zip, is_duplicate_snapshot, perform_zip_creation, TM_DIR, get_tracked_folders
from ui import ProgressWindow, ItemCard, AndroidToggle, ActionButton, center_window, set_window_icon, COLORS, show_home_window

def hide_console():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 0)

flavor_path = os.path.join(get_base_path(), "build_flavor.txt")
IS_VIP = False
if os.path.exists(flavor_path):
    with open(flavor_path, "r") as f:
        IS_VIP = (f.read().strip() == "VIP")

ICON_NAME = "vip_app_icon.ico" if IS_VIP else "app_icon.ico"

def execute_snapshot(target_dir, custom_name="", prefix="Snapshot", use_gui=True, is_fav=False, force=False):
    from core import create_timeignore
    create_timeignore(target_dir)
    all_files = get_files_to_zip(target_dir)
    if not force and is_duplicate_snapshot(target_dir, all_files, prefix):
        if use_gui:
            if not messagebox.askyesno("Duplicate Found", f"A {prefix} with identical files already exists. Create anyway?"): os._exit(0)
        else: print("Identical snapshot exists. Use -f or --force to bypass."); os._exit(0)

    try:
        prog_win = ProgressWindow("Pre-Restore Backup" if prefix == "Backup" else f"Creating {prefix}", "Creating Safety Backup..." if prefix == "Backup" else f"Zipping {len(all_files)} files...") if use_gui else None
        def prog_cb(val):
            if prog_win: prog_win.update(val)
        
        snapshot_name, total_files = perform_zip_creation(target_dir, all_files, custom_name, prefix, progress_callback=prog_cb, is_fav=is_fav)
        if prog_win: prog_win.close()
        if use_gui and prefix != "Backup": messagebox.showinfo("TimeMachine", f"{prefix} Created Successfully!\n\nName: {snapshot_name}\nFiles Saved: {total_files}")
        elif not use_gui: print(f"Success! Created {snapshot_name} ({total_files} items)")
        if prefix != "Backup": os._exit(0)
    except Exception as e:
        if use_gui: messagebox.showerror("Error", f"Failed: {e}")
        else: print(f"Error: {e}")
        os._exit(1)

def execute_restore(target_dir, target_snap, use_gui=True, make_backup=True, keep_untracked=True):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path):
        if use_gui: messagebox.showerror("Error", "No snapshots found.")
        else: print("Error: No .TimeMachine folder found.")
        os._exit(1)
        
    snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
    
    # Matches "22", "Snapshot_22", or the full filename
    matches = [
        f for f in snapshots 
        if f == target_snap 
        or f.startswith(f"Snapshot_{target_snap}_")
        or f.startswith(f"Backup_{target_snap}_")
        or f.startswith(f"{target_snap}_")
    ]
    
    if matches: 
        target_snap = sorted(matches)[-1] 
    else:
        if use_gui: messagebox.showerror("Error", f"Snapshot '{target_snap}' not found.")
        else: print(f"Error: Snapshot '{target_snap}' not found.")
        os._exit(1)

    if make_backup: execute_snapshot(target_dir, prefix="Backup", use_gui=use_gui, is_fav=False, force=True)
    prog_win = ProgressWindow("Restoring Data", f"Deploying {target_snap}...") if use_gui else None
    
    try:
        if keep_untracked:
            files_to_delete = get_files_to_zip(target_dir)
            for i, file_path in enumerate(files_to_delete):
                if os.path.isfile(file_path):
                    try: os.unlink(file_path)
                    except PermissionError: os.chmod(file_path, 128); os.unlink(file_path)
                if use_gui and len(files_to_delete) > 0: prog_win.update((i / len(files_to_delete)) * 40)
            for root, dirs, files in os.walk(target_dir, topdown=False):
                if TM_DIR in root.split(os.sep): continue
                for d in dirs:
                    try: os.rmdir(os.path.join(root, d)) 
                    except OSError: pass 
        else:
            items = [i for i in os.listdir(target_dir) if i != TM_DIR]
            for i, item in enumerate(items):
                path = os.path.join(target_dir, item)
                try:
                    if os.path.isdir(path): shutil.rmtree(path, onerror=lambda f, p, e: (os.chmod(p, 128), f(p)))
                    else: 
                        try: os.unlink(path)
                        except PermissionError: os.chmod(path, 128); os.unlink(path)
                except Exception: pass
                if use_gui and len(items) > 0: prog_win.update((i / len(items)) * 40) 
            
        with zipfile.ZipFile(os.path.join(tm_path, target_snap), 'r') as zipf:
            members = zipf.infolist()
            for i, member in enumerate(members):
                zipf.extract(member, target_dir)
                if use_gui and len(members) > 0: prog_win.update(40 + ((i / len(members)) * 60)) 

        if prog_win: prog_win.close()
        if use_gui: messagebox.showinfo("Success", f"Project successfully restored!\n\nLoaded: {target_snap}")
        else: print(f"Successfully restored from {target_snap}")
        os._exit(0) 
    except Exception as e:
        if prog_win: prog_win.close()
        if use_gui: messagebox.showerror("Restore Error", f"Failed to restore: {e}")
        else: print(f"Error: {e}")
        os._exit(1)

def print_cli_help():
    print("\n=== FusionHex TimeMachine CLI ===")
    print(" \n tm snapshot [name]  : Create snapshot (-f to force, --fav)")
    print(" \n tm restore <ID>     : Restore a snapshot (--wipe to delete untracked) e.g :  tm restore Snapshot_23_20260831_014021_fav.zip (By Default it makes a backup and keep untracked files)")
    print(" \n tm list             : List all snapshots in current dir")
    print(" \n tm projects         : List all global tracked folders")
    print(" \n tm ignore <pattern> : Add pattern to .timeignore (--overwrite) e.g : credentials/password.txt" )

class FusionParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"\nError: {message}")
        print_cli_help()
        sys.exit(2)

def main_execution():
    parser = FusionParser(prog="tm" if IS_VIP else "TimeMachine", description="FusionHex TimeMachine")
    subparsers = parser.add_subparsers(dest="command")

    p_ctx_create = subparsers.add_parser("_ctx_create")
    p_ctx_create.add_argument("path"); p_ctx_create.add_argument("--fav", action="store_true")
    p_ctx_restore = subparsers.add_parser("_ctx_restore")
    p_ctx_restore.add_argument("path")

    if IS_VIP:
        p_snap = subparsers.add_parser("snapshot")
        p_snap.add_argument("name", nargs="?", default="")
        p_snap.add_argument("--fav", action="store_true"); p_snap.add_argument("-f", "--force", action="store_true")
        p_list = subparsers.add_parser("list")
        p_projects = subparsers.add_parser("projects")
        p_ignore = subparsers.add_parser("ignore")
        p_ignore.add_argument("pattern"); p_ignore.add_argument("--overwrite", action="store_true")
        p_restore = subparsers.add_parser("restore")
        p_restore.add_argument("id_or_name"); p_restore.add_argument("--wipe", action="store_true")
        subparsers.add_parser("commands"); subparsers.add_parser("help")

    args, unknown = parser.parse_known_args()

    if not args.command:
        hide_console()
        root = tk.Tk()
        show_home_window(root, IS_VIP, ICON_NAME)
        root.mainloop()

    elif args.command in ["_ctx_create", "_ctx_restore"]:
        hide_console() 
        root = tk.Tk(); root.withdraw(); set_window_icon(root, ICON_NAME)
        
        target = args.path.strip('" ') if args.path else os.getcwd()
        if os.path.basename(target) == TM_DIR: target = os.path.dirname(target)
            
        if args.command == "_ctx_create":
            threading.Thread(target=execute_snapshot, args=(target, "", "Snapshot", True, args.fav, False), daemon=True).start()
            root.mainloop()
            
        elif args.command == "_ctx_restore":
            tm_path = os.path.join(target, TM_DIR)
            if not os.path.exists(tm_path): messagebox.showerror("Error", "No snapshots here."); os._exit(0)
            
            snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
            snapshots.sort(key=lambda x: int(x.split("_")[1]) if "_" in x else 0, reverse=True)
            
            top = tk.Toplevel(); top.title("FusionHex - Restore Center")
            center_window(top, 620, 650); top.configure(bg=COLORS["bg"]); set_window_icon(top, ICON_NAME)
            top.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
            
            tk.Label(top, text="Select Snapshot to Restore", font=("Segoe UI", 16, "bold"), bg=COLORS["bg"], fg=COLORS["primary"]).pack(pady=(20, 10))
            
            list_frame = tk.Frame(top, bg=COLORS["bg"])
            list_frame.pack(fill="both", expand=True, padx=20, pady=5)
            
            canvas = tk.Canvas(list_frame, bg=COLORS["bg"], highlightthickness=0)
            style = ttk.Style(); style.theme_use('clam')
            style.configure("Dark.Vertical.TScrollbar", background=COLORS["border"], troughcolor=COLORS["bg"], bordercolor=COLORS["bg"], arrowcolor=COLORS["primary"], relief="flat", borderwidth=0)
            
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
            scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])

            # Dynamically centers the restore cards as well
            canvas_window = canvas.create_window((280, 0), window=scrollable_frame, anchor="n")
            
            def on_configure(e):
                canvas.itemconfig(canvas_window, width=e.width)
                canvas.configure(scrollregion=canvas.bbox("all"))
                
            canvas.bind("<Configure>", on_configure)
            top.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            
            canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
            
            selected_snapshot = [None]
            cards = []
            
            def handle_card_select(val):
                selected_snapshot[0] = val
                for c in cards: c.set_selected(c.value == val)

            for s in snapshots:
                icon = "⭐" if "_FAV" in s else ("🛡️" if "Backup_" in s else "📦")
                card = ItemCard(scrollable_frame, 550, 45, f"{icon}   {s}", s, handle_card_select)
                card.pack(pady=5, anchor="center")
                cards.append(card)
            
            options_frame = tk.Frame(top, bg=COLORS["bg"])
            options_frame.pack(fill="x", padx=35, pady=(15, 20))
            
            toggle_state = [True]
            AndroidToggle(options_frame, command=lambda s: toggle_state.__setitem__(0, s), initial_state=True).pack(side="left", padx=(0, 10))
            tk.Label(options_frame, text="Safe Restore (Keep untracked items like venv)", bg=COLORS["bg"], fg=COLORS["secondary"], font=("Segoe UI", 10)).pack(side="left")

            def do_restore():
                ch = selected_snapshot[0]
                if ch:
                    if messagebox.askyesno("Confirm", f"Restore:\n\n{ch}\n\n(A backup will be created first)."):
                        top.destroy()
                        threading.Thread(target=execute_restore, args=(target, ch, True, True, toggle_state[0]), daemon=True).start()
                else: messagebox.showwarning("Warning", "Please click on a snapshot first.")

            ActionButton(top, 500, 45, "RESTORE SELECTED", COLORS["danger"], COLORS["danger_hover"], "white", command=do_restore).pack(pady=(0, 25))
            root.mainloop()

    elif IS_VIP:
        cwd = os.getcwd()
        if os.path.basename(cwd) == TM_DIR: cwd = os.path.dirname(cwd)

        if args.command in ["commands", "help"]:
            print_cli_help()
            os._exit(0)
        elif args.command == "snapshot": execute_snapshot(cwd, custom_name=args.name, use_gui=False, is_fav=args.fav, force=args.force)
        elif args.command == "projects":
            folders = get_tracked_folders()
            if not folders: print("No tracked projects found.")
            else:
                print("\n=== Tracked TimeMachine Projects ===")
                for f in folders: print(f" -> {f}")
        elif args.command == "list":
            tm_path = os.path.join(cwd, TM_DIR)
            if not os.path.exists(tm_path):
                print("No snapshots found here.")
                os._exit(0)

            snapshots = [f for f in os.listdir(tm_path) if f.endswith(".zip")]
            snapshots.sort(key=lambda x: int(x.split("_")[1]) if "_" in x and x.split("_")[1].isdigit() else 0, reverse=True)

            if not snapshots:
                print("No snapshots found here.")
                os._exit(0)

            print("\n=== Snapshots in Current Directory ===")
            for s in snapshots:
                size_mb = round(os.path.getsize(os.path.join(tm_path, s)) / (1024 * 1024), 2)
                parts = s.replace(".zip", "").split("_")
                
                # Extracts just the number (e.g. "22" from "Snapshot_22_...")
                snap_num = parts[1] if len(parts) > 1 and parts[1].isdigit() else parts[0]
                
                print(f"  [{snap_num}]  {s} ({size_mb} MB)")
            print("======================================\n")
        elif args.command == "ignore":
            ignore_path = os.path.join(cwd, ".timeignore")
            
            # If overwriting or file doesn't exist, create fresh
            if args.overwrite or not os.path.exists(ignore_path):
                with open(ignore_path, "w") as f: 
                    f.write(f"# FusionHex TimeMachine Ignore File\n{args.pattern}\n")
            else:
                # Read the file first to check the last character
                with open(ignore_path, "r") as f:
                    content = f.read()
                
                # Append safely
                with open(ignore_path, "a") as f:
                    if content and not content.endswith("\n"):
                        f.write("\n") # Force a new line if it's missing!
                    f.write(f"{args.pattern}\n")
                    
            print(f"Successfully added {args.pattern} to .timeignore")
        elif args.command == "restore": execute_restore(cwd, args.id_or_name, use_gui=False, make_backup=True, keep_untracked=not args.wipe)

if __name__ == "__main__":
    try:
        main_execution()
    except Exception as e:
        error_msg = f"A fatal error occurred:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("TimeMachine Critical Error", error_msg)
        sys.exit(1)