<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=header&text=Exporter&fontSize=90&fontAlignY=35&desc=A%20Safe,%20Interactive%20File%20Transfer%20Utility&descAlignY=51&descSize=20"/>
</p>

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active--development-brightgreen)
![Standard Library](https://img.shields.io/badge/dependencies-Standard_Library_First-orange)

**Fast, cross-platform file copying with robust safeguards and drag-and-drop support.**

</div>

---

## 📖 About

**Exporter** is a production-grade, interactive command-line utility for moving and copying files/folders across Windows, macOS, and Linux. Built for developers and power users, it bridges the gap between the speed of the terminal and the visual convenience of a GUI. 

Unlike standard `cp` or `copy` commands, Exporter actively protects your data with a **non-destructive Undo system**, visual progress bars, and graceful handling of massive file transfers.

---

## ✨ Killer Features

- 🔄 **Smart Undo System:** Accidentally overwrite a file? Exporter actively backs up overwritten files and can restore them instantly if you hit Undo.
- 🖱️ **Drag & Drop Ready:** Robust path parsing natively handles dragging multiple files from Windows File Explorer or macOS Finder directly into the terminal—spaces and quotes are handled flawlessly.
- 📊 **Visual Progress Bars:** Track massive file and folder transfers with accurate, byte-based progress indicators.
- 🛡️ **Failsafe Operations:** Safely handle interruptions. If you hit `Ctrl+C` halfway through a 50GB transfer, Exporter automatically cleans up the corrupted partial file.
- 🔗 **Symlink Preservation:** Intelligently detects and preserves symbolic links rather than duplicating underlying files.
- 🧩 **Zero Hard Dependencies:** Runs entirely on Python's standard library out of the box (with optional enhanced trash support).

---

## 💻 Installation

Clone the repository and run the script directly. No complex setup is required.

```bash
git clone [https://github.com/SS-Sauron/Exporter.git](https://github.com/SS-Sauron/Exporter.git)
cd Exporter
```

(Optional but Highly Recommended): Install send2trash to allow Exporter's Undo feature to safely route deleted files to your OS Recycle Bin/Trash instead of permanently deleting them.

```Bash
pip install send2trash
```

🚀 Usage

Simply run the script to launch the interactive Exporter shell:
```Bash

python exporter.py
```
The Interactive Shell

Instead of memorizing complex command-line flags, Exporter guides you through a clean, persistent terminal UI:
```Plaintext

==================================================
📂 TARGET: C:\Users\YourName\Desktop
   [1] Copy files/folders (any number, drag‑and‑drop or list)
   [2] Settings
   [3] Undo last copy
   [0] Exit
Your choice: 
```
---
Workflow Example:

    Press 1 to initiate a copy.

    Drag and drop 5 different files/folders directly from your file manager into the terminal.

    Press Enter. Exporter calculates the sizes, shows a progress bar, handles conflicts safely, and logs the transaction!

    Made a mistake? Press 3 to instantly roll back the entire batch.
---

🛠️ Tech Stack

    Language: Python 3.8+

    Architecture: Standard Library (os, shutil, pathlib, shlex, dataclasses)

    Supported OS: Windows, Linux, macOS
---

🤝 Contributing

Contributions, issues, and feature requests are welcome!

    Fork the repo

    Create your feature branch (git checkout -b feature/amazing-feature)

    Commit your changes (git commit -m 'Add some amazing feature')

    Push to the branch (git push origin feature/amazing-feature)

    Open a Pull Request
---

📜 License

Distributed under the MIT License. See LICENSE for details.

