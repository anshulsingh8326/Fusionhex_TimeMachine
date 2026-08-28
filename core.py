import os
import sys
import shutil
import zipfile
import stat
import fnmatch
import json
from datetime import datetime

TM_DIR = ".TimeMachine"

def get_base_path():
    return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))

def hide_folder(path):
    try: ctypes = __import__('ctypes'); ctypes.windll.kernel32.SetFileAttributesW(str(path), 2)
    except Exception: pass

# --- GLOBAL TRACKING LOGIC ---
def get_global_data_path():
    appdata = os.path.join(os.getenv('LOCALAPPDATA'), 'FusionHex_TimeMachine')
    os.makedirs(appdata, exist_ok=True)
    return os.path.join(appdata, 'tracked_folders.json')

def add_tracked_folder(target_dir):
    data_path = get_global_data_path()
    folders = []
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r') as f: folders = json.load(f)
        except Exception: pass
    if target_dir not in folders:
        folders.append(target_dir)
        with open(data_path, 'w') as f: json.dump(folders, f)

def get_tracked_folders():
    data_path = get_global_data_path()
    if not os.path.exists(data_path): return []
    try:
        with open(data_path, 'r') as f: folders = json.load(f)
        # Auto-cleanup deleted/missing projects
        valid = [f for f in folders if os.path.exists(os.path.join(f, TM_DIR))]
        if len(valid) != len(folders):
            with open(data_path, 'w') as f: json.dump(valid, f)
        return valid
    except Exception: return []
# -----------------------------

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

def create_timeignore(target_dir):
    ignore_path = os.path.join(target_dir, ".timeignore")
    if not os.path.exists(ignore_path):
        with open(ignore_path, "w") as f: 
            f.write("# FusionHex TimeMachine Ignore File\n# node_modules/\n# build/\n# dist/\n# venv/\n# .git/\n# __pycache__/\n# *.mp4\n")

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

def get_next_index(target_dir, prefix):
    tm_path = os.path.join(target_dir, TM_DIR)
    if not os.path.exists(tm_path): return 1
    indices = [int(f.split("_")[1]) for f in os.listdir(tm_path) if f.startswith(prefix) and f.endswith(".zip") and "_" in f]
    return max(indices) + 1 if indices else 1

def perform_zip_creation(target_dir, all_files, custom_name, prefix, progress_callback=None, is_fav=False):
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
    
    with zipfile.ZipFile(snapshot_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if total_files > 0:
            for i, file_path in enumerate(all_files):
                zipf.write(file_path, os.path.relpath(file_path, target_dir))
                if progress_callback and i % max(1, total_files // 100) == 0:
                    progress_callback((i / total_files) * 100)
    
    if progress_callback: progress_callback(100)
    add_tracked_folder(target_dir) # Save to ledger
    return snapshot_name, total_files