<!-- README.md - Copy and paste this entire block into your README.md file -->

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=header&text=Exporter&fontSize=90&fontAlignY=35&desc=A%20modern,%20reliable%20file%20transfer%20utility&descAlignY=51&descSize=20"/>
</p>

# 🚀 Exporter

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active--development-brightgreen)
![GitHub last commit](https://img.shields.io/github/last-commit/SS-Sauron/Exporter)
![GitHub code size](https://img.shields.io/github/languages/code-size/SS-Sauron/Exporter)

**Fast, cross-platform file copying made simple.**

</div>

---

## 📖 About

Exporter is a lightweight, dependency‑free Python utility for moving and copying files across Windows, macOS, and Linux. Built for developers and power users who need reliable file operations without the bloat of a full file manager.

---

## ✨ Features

- ⚡ **Blazing fast** – uses optimised system calls
- 🖥️ **Cross‑platform** – works on Windows, Linux, macOS
- 🛡️ **Robust error handling** – clear feedback for permissions, disk space, etc.
- 🧩 **No external dependencies** – only Python’s standard library
- 📦 **Simple CLI** – intuitive arguments and help text

---

## 🛠️ Tech Stack

- **Language:** Python 3.6+
- **Libraries:** `os`, `shutil`, `pathlib`, `argparse`
- **Supported OS:** Windows, Linux, macOS

---

## 💻 Installation

```bash
git clone https://github.com/SS-Sauron/Exporter.git
cd Exporter

# No extra installation required – just Python.
```

🚀 Usage
bash
```
# Copy a single file
python export.py --source "document.pdf" --destination "./backup/"

# Copy and rename
python export.py --source "config.ini" --destination "config_backup.ini"

# Copy multiple files
python export.py --source file1.txt file2.txt --destination "./archive/"

# Show help
python export.py --help
```

Example output:
text
```
Exporting file 'data.csv'...
✅ Success! Copied to '/backups/data.csv'
```

---

🤝 Contributing

Contributions are welcome!

    Fork the repo

    Create a branch (git checkout -b feature/amazing)

    Commit changes (git commit -m 'Add amazing feature')

    Push to branch (git push origin feature/amazing)

    Open a Pull Request

---

📜 License

Distributed under the MIT License. See LICENSE for details.
