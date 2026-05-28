![Exporter Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=header&text=Exporter&fontSize=90&fontAlignY=35&desc=A%20Safe,%20Interactive%20File%20Transfer%20Utility&descAlignY=51&descSize=20)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/SS-Sauron/Exporter)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active--development-brightgreen)](https://github.com/SS-Sauron/Exporter)
[![Dependencies](https://img.shields.io/badge/dependencies-Standard_Library_First-orange)](https://github.com/SS-Sauron/Exporter)

**Fast, cross-platform file copying with robust safeguards and drag‑and‑drop support.**

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
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

## ✨ Features

- 🔄 **Smart Undo System** – Accidentally overwrite a file? Exporter backs up overwritten files automatically and can restore them instantly if you hit Undo.
- 🖱️ **Drag & Drop Ready** – Robust path parsing handles dragging multiple files from Windows File Explorer or macOS Finder directly into the terminal – spaces and quotes are handled flawlessly.
- 📊 **Visual Progress Bars** – Track large file and folder transfers with accurate, byte‑based progress indicators.
- 🛡️ **Failsafe Operations** – Hit `Ctrl+C` halfway through a large transfer? Exporter automatically cleans up the corrupted partial file.
- 🔗 **Symlink Preservation** – Intelligently detects and preserves symbolic links rather than duplicating the underlying files.
- 🧩 **Zero Hard Dependencies** – Runs entirely on Python's standard library out of the box (with optional enhanced trash support).

---

## 💻 Installation

Clone the repository and install using one of the methods below:

```bash
git clone https://github.com/SS-Sauron/Exporter.git
cd Exporter
```

**Standard Installation:**
```bash
pip install .
```

**Recommended — With Safe Undo / Recycle Bin Support:**

Installs the optional `send2trash` dependency so that undone files are sent to your OS trash bin instead of being permanently erased.
```bash
pip install .[trash]
```

**Development Mode:**

For those who plan to modify the source and want changes to reflect instantly:
```bash
pip install -e .[trash]
```

---

## 🚀 Quick Start

Once installed, launch Exporter from **any directory** in your terminal:

```bash
exporter
```

You'll be greeted by the interactive dashboard:

```
==================================================
📂 TARGET: /home/user/Desktop
   [1] Copy files/folders (any number, drag‑and‑drop or list)
   [2] Settings
   [3] Undo last copy
   [0] Exit
Your choice:
```

> 💡 **Pro-Tip:** Press `1`, then drag & drop files/folders from your native file manager directly into the terminal window. Press `Enter` to process. Made a mistake? Type `3` to instantly roll back the entire batch!

---

## 🖥️ Usage

### The Interactive Shell

Instead of memorizing complex command‑line flags, Exporter guides you through a persistent terminal UI.

1. Press `1` to start a copy operation.
2. Drag and drop any number of different files/folders into the terminal.
3. Press `Enter`. Exporter calculates sizes, renders an active progress bar, manages conflicts safely, and logs the transaction.

### Logging

All copy transactions and runtime errors are quietly tracked for your review at:

```
~/.exporter_log.txt
```

---

## ⚙️ Configuration

Press `2` from the main menu to tweak active session rules:

- **Target directory** – Define exactly where your files should land (defaults to your Desktop).
- **Auto‑replace** – Toggle whether Exporter prompts you before overwriting existing files.
- **Recycle bin undo** – Toggle whether the undo routine permanently deletes files or routes them safely to the system trash.

---

## 🛠️ Tech Stack

| Component | Detail |
|---|---|
| **Language** | Python 3.8+ |
| **Core Engine** | Pure Python Standard Library (`os`, `shutil`, `pathlib`, `shlex`, `dataclasses`) |
| **Optional Enhancement** | `send2trash` for native OS Recycle Bin/Trash integration |
| **Platforms** | Windows, Linux, macOS |

---

## 🤝 Contributing

Contributions, issues, and feature requests are always welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for code style guidelines and debugging notes before opening a pull request.

1. Fork the repo.
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request.

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
