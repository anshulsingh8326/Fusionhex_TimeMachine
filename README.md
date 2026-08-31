# FusionHex TimeMachine

**Instant, zero-friction folder snapshots for Windows.**

Create complete project backups directly from the Windows context menu and restore them whenever you need.

FusionHex TimeMachine is a lightweight snapshot and local versioning utility for Windows. Instead of tracking file changes like traditional version control systems, TimeMachine creates complete, independent `.zip` snapshots of your project.

Whether you're trying a risky refactor, modifying game assets, testing shaders, editing 3D models, or simply want a restore point before making changes, TimeMachine lets you return your project to a previous state in seconds.

---

# Features

## One-Click Snapshots

Create snapshots directly from the Windows Explorer context menu. No repository, or configuration required.

- Automatic sequential snapshots (`Snapshot_1`, `Snapshot_2`, ...)
    
- Favorite snapshots (`Snapshot_1_FAV`) for important milestones
    
- Fast snapshot creation with minimal overhead
    

---

## Self-Contained Backups

Each snapshot is stored as a standalone `.zip` archive inside a hidden `.TimeMachine` folder within the project.

Unlike differential backup systems:

- Every snapshot is independent
    
- No merge conflicts
    
- No dependency on previous snapshots
    
- No proprietary database
    
- A damaged snapshot does not affect the rest of your history
    

---

## `.timeignore` Support

TimeMachine supports `.gitignore`-style rules through a `.timeignore` file.

Use it to exclude files and folders that don't belong in snapshots, such as:

- `node_modules/`
    
- `build/`
    
- `dist/`
    
- `Library/`
    
- `Temp/`
    
- `Logs/`
    
- `venv/`
    
- `.git/`
    
- `__pycache__/`
    
- Large media files
    
- Temporary files
    

---

## Safe Restore

Before restoring a snapshot, TimeMachine automatically creates a backup of your current workspace.

By default, folders such as virtual environments, dependency directories, caches, and other items that are not part of the snapshot are preserved if you toggle the Safe Restore in Restore Window.


---

## Project Dashboard

TimeMachine keeps track of every project where snapshots have been created.

Open any tracked project directly without searching through your drives by Opening the TimeMachine Application.

---

## Windows Explorer Integration

TimeMachine integrates directly into Windows Explorer.

Right-click any folder to:

- Create a snapshot
    
- Create a favorite snapshot
    
- Open the Restore Center
    

No Git repository is required.

---

# `.timeignore`

When a snapshot is created, TimeMachine looks for a `.timeignore` file in the project root.

If one isn't found, a default template is created automatically.

Example:

```text
# Directories
node_modules/
dist/
build/
Library/
Temp/
Logs/
venv/
.git/
__pycache__/

# File Types
*.mp4
*.iso
*.obj
*.tmp
```

---

# Project Structure

```text
FusionHex_TimeMachine/
├── assets/
│   ├── app_icon.ico
│   ├── vip_app_icon.ico
│   ├── create.ico
│   ├── fav.ico
│   └── restore.ico
├── build.bat
├── config.json
├── core.py
├── main.py
├── setup.iss
└── ui.py
```

---

# Building from Source

The included `build.bat` script automates the entire build process for both the Free and VIP editions.

## Prerequisites

Install the following before building:

### Python 3.10+

Ensure both `python` and `pip` are available from the command line.

### Inno Setup 6

Required to package the application into a Windows installer.

Download:

[https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

---

## Configure Inno Setup

Open `build.bat` and locate the line that launches `ISCC.exe` (around line 45).

Update the path if your installation is located elsewhere.

Example:

```bat
"D:\Program Files\Inno Setup 6\ISCC.exe"
```

Common installation paths include:

```text
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

or

```text
D:\Program Files\Inno Setup 6\ISCC.exe
```

---

## Build Instructions

1. Run `build.bat`.
    
2. Select the edition to build.
    

| Option | Edition      | Output                       |
| ------ | ------------ | ---------------------------- |
| **1**  | VIP Edition  | `TimeMachine_VIP_Setup.exe`  |
| **2**  | Free Edition | `TimeMachine_Free_Setup.exe` |

The build script automatically:

- Stops any running TimeMachine processes
    
- Creates a Python virtual environment if needed
    
- Installs PyInstaller
    
- Reads version information from `config.json`
    
- Configures the selected edition
    
- Builds the executable
    
- Packages the installer with Inno Setup
    
- Removes temporary build files
    

---

## Build Output

The generated installer will be placed in:

```text
dist/
├── TimeMachine_Free_Setup.exe
└── TimeMachine_VIP_Setup.exe
```

Only the installer for the selected edition is generated.

---

# Use Cases

TimeMachine is useful whenever you want an easy way to save and restore the state of a project.

Common examples include:

- Unity projects
    
- Unreal Engine projects
    
- Blender projects
    
- Photoshop projects
    
- Web development
    
- Python applications
    
- Any folder where you want a quick restore point before making changes
    

If you don't need commits, branches, or collaborative workflows, creating full project snapshots is often the simpler solution.

---

# License

Released under the MIT License.

See the `LICENSE` file for details.