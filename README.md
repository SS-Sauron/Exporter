<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=header&text=Exporter&fontSize=90&fontAlignY=35&desc=A%20Safe,%20Interactive%20File%20Transfer%20Utility&descAlignY=51&descSize=20"/>
</p>

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active--development-brightgreen)
![Dependencies](https://img.shields.io/badge/dependencies-Standard_Library_First-orange)

**Fast, cross-platform file copying with robust safeguards and drag‑and‑drop support.**

</div>

---

## 📖 Table of Contents

- [About](#-about)
- [Killer Features](#-killer-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Tech Stack](#-tech-stack)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 About

**Exporter** is a production‑grade, interactive command‑line utility for moving and copying files and folders across Windows, macOS, and Linux. It bridges the gap between the speed of the terminal and the visual convenience of a GUI.

Unlike standard `cp` or `copy` commands, Exporter actively protects your data with a **non‑destructive Undo system**, visual progress bars, and graceful handling of massive file transfers.

---

## ✨ Killer Features

- 🔄 **Smart Undo System** – Accidentally overwrite a file? Exporter backs up overwritten files automatically and can restore them instantly if you hit Undo.
- 🖱️ **Drag & Drop Ready** – Robust path parsing handles dragging multiple files from Windows File Explorer or macOS Finder directly into the terminal – spaces and quotes are handled flawlessly.
- 📊 **Visual Progress Bars** – Track large file and folder transfers with accurate, byte‑based progress indicators.
- 🛡️ **Failsafe Operations** – Safely handle interruptions. Hit `Ctrl+C` halfway through a 50 GB transfer? Exporter automatically cleans up the corrupted partial file.
- 🔗 **Symlink Preservation** – Intelligently detects and preserves symbolic links rather than duplicating the underlying files.
- 🧩 **Zero Hard Dependencies** – Runs entirely on Python’s standard library out of the box (with optional enhanced trash support).

---

## 💻 Installation

Clone the repository and run the script directly. No complex setup is required.

```bash
git clone https://github.com/SS-Sauron/Exporter.git
cd Exporter
```
Optional but highly recommended:
Install send2trash to allow Exporter’s Undo feature to safely route deleted files to your operating system’s Recycle Bin / Trash instead of permanently deleting them.
```bash

pip install send2trash
```
---
🚀 Quick Start

Once installed, launch the interactive shell with:
```bash

python exporter.py
```
You’ll see a clean menu:
```text

==================================================
📂 TARGET: C:\Users\YourName\Desktop
   [1] Copy files/folders (any number, drag‑and‑drop or list)
   [2] Settings
   [3] Undo last copy
   [0] Exit
Your choice: 

# Press 1, then drag & drop files/folders from your file manager directly into the terminal. Press Enter – Exporter does the rest. Made a mistake? Press 3 to instantly roll back the entire batch.
```
---
🛠️ Usage
The Interactive Shell

Instead of memorizing complex command‑line flags, Exporter guides you through a persistent terminal UI.

Workflow example:

    1.Press 1 to start a copy operation.

    2.Drag and drop 5 different files/folders from your file manager into the terminal.

    3.Press Enter. Exporter calculates sizes, shows a progress bar, handles conflicts safely, and logs the transaction.

    4.Made a mistake? Press 3 to instantly roll back the entire batch.

Logging

All copy operations are logged to ~/.exporter_log.txt (in your home directory). You can review this file at any time.
---
⚙️ Configuration

Press 2 from the main menu to change settings:

    Target directory – where copied files/folders will be placed (defaults to your Desktop).

    Auto‑replace – if OFF (default), Exporter asks before overwriting existing files.

    Recycle bin undo – if ON, Undo moves newly copied items to the trash (requires send2trash).

    Settings are remembered for the current session only – relaunching the script resets to defaults.
---
🛠️ Tech Stack

    Language: Python 3.8+

    Libraries: Standard Library only (os, shutil, pathlib, shlex, dataclasses) – no external dependencies required.

    Optional enhancement: send2trash for recycle bin integration.

    Supported OS: Windows, Linux, macOS
---
🤝 Contributing

Contributions, issues, and feature requests are welcome!

    Fork the repo.

    Create your feature branch (git checkout -b feature/amazing-feature).

    Commit your changes (git commit -m 'Add some amazing feature').

    Push to the branch (git push origin feature/amazing-feature).

    Open a Pull Request.

Please read our CONTRIBUTING.md for code style and guidelines.
---
📜 License

Distributed under the MIT License. See the LICENSE file for details.
