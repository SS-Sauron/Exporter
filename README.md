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

**Exporter** is a production‑grade, interactive command‑line utility for moving and copying files and folders across Windows, macOS, and Linux[cite: 5]. It bridges the gap between the speed of the terminal and the visual convenience of a GUI[cite: 5].

Unlike standard `cp` or `copy` commands, Exporter actively protects your data with a **non‑destructive Undo system**, visual progress bars, and graceful handling of massive file transfers[cite: 5].

---

## ✨ Killer Features

- 🔄 **Smart Undo System** – Accidentally overwrite a file? Exporter backs up overwritten files automatically and can restore them instantly if you hit Undo[cite: 5].
- 🖱️ **Drag & Drop Ready** – Robust path parsing handles dragging multiple files from Windows File Explorer or macOS Finder directly into the terminal – spaces and quotes are handled flawlessly[cite: 5].
- 📊 **Visual Progress Bars** – Track large file and folder transfers with accurate, byte‑based progress indicators[cite: 5].
- 🛡️ **Failsafe Operations** – Safely handle interruptions. Hit `Ctrl+C` halfway through a large transfer? Exporter automatically cleans up the corrupted partial file[cite: 4, 5].
- 🔗 **Symlink Preservation** – Intelligently detects and preserves symbolic links rather than duplicating the underlying files[cite: 5].
- 🧩 **Zero Hard Dependencies** – Runs entirely on Python’s standard library out of the box (with optional enhanced trash support)[cite: 4, 5].

---
## 💻 Installation

You can now install Exporter locally as a system-wide command-line utility.

1. **Clone the repository:**

```bash
   git clone [https://github.com/SS-Sauron/Exporter.git](https://github.com/SS-Sauron/Exporter.git)
   cd Exporter
```

2. **Install the package:**
Choose one of the following installation methods depending on your workflow:

* **Standard Installation:**

```bash
     pip install .
     ```
* **Recommended Installation (With Safe Undo / Recycle Bin Support):**
This installs the optional `send2trash` dependency so that undone files are sent to your OS trash bin instead of being permanently erased[cite: 2, 3].
```bash
     pip install .[trash]
     ```
* **Development Mode:**
If you plan to modify the source code and want changes to reflect instantly:
```bash
     pip install -e .[trash]
     ```

---

## 🚀 Quick Start

Once installed via `setup.py`, you can launch the application from **any directory** in your terminal simply by typing:

```bash
exporter

```

You’ll immediately be greeted by the interactive dashboard:

```text
==================================================
📂 TARGET: /home/user/Desktop
   [1] Copy files/folders (any number, drag‑and‑drop or list)
   [2] Settings
   [3] Undo last copy
   [0] Exit
Your choice: 

```

> 💡 **Pro-Tip:** Press `1`, then drag & drop files/folders from your native file manager directly into the terminal window. Press `Enter` to process. Made an unexpected mistake? Type `3` to instantly roll back the entire batch!
> 
> 

---

## 🛠️ Usage

### The Interactive Shell

Instead of memorizing complex command‑line flags, Exporter guides you through a persistent terminal UI.

1. Press `1` to start a copy operation.


2. Drag and drop any number of different files/folders into the terminal.


3. Press `Enter`. Exporter calculates sizes, renders an active progress bar, manages conflicts safely, and logs the transaction.



### Logging

All copy transactions and runtime errors are quietly tracked for your review at:

* `~/.exporter_log.txt` *(located in your user home directory)*


---

## ⚙️ Configuration

Press `2` from the main menu to tweak active session rules:

* **Target directory:** Define exactly where your files should land (defaults to your Desktop).


* **Auto‑replace:** Toggle whether Exporter prompts you safely before overwriting existing destination elements.


* **Recycle bin undo:** Toggle whether the undo routine permanently deletes files or routes them safely to the system trash.



---

## 🛠️ Tech Stack

* **Language:** Python 3.8+


* **Core Engine:** Pure Standard Python Library (`os`, `shutil`, `pathlib`, `shlex`, `dataclasses`).


* **Optional Enhancements:** `send2trash` for native OS Recycle Bin/Trash integration.


* **Supported Environments:** Linux, Windows, macOS.



---

## 🤝 Contributing

Contributions, issues, and feature requests are always welcome!

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).


3. Commit your changes (`git commit -m 'Add some amazing feature'`).


4. Push to the branch (`git push origin feature/amazing-feature`).


5. Open a Pull Request.



Please read our [CONTRIBUTING.md](https://www.google.com/search?q=CONTRIBUTING.md) for structural code styles and explicit debugging guidelines.

---

## 📜 License

Distributed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for more information.

```

```
