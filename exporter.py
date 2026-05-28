#!/usr/bin/env python3
"""
Exporter – Safe, interactive file/folder copier with undo and progress bars.
Uses only standard library; optional send2trash if installed.
"""

import os
import sys
import shutil
import shlex
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ==================== CONSTANTS ====================
CHUNK_SIZE = 1024 * 1024          # 1 MB
PROGRESS_BAR_LEN = 30
BACKUP_DIR_NAME = ".exporter_backups"
LOG_FILE = Path.home() / ".exporter_log.txt"          # User's home directory – always writable
BACKUP_RETENTION_COUNT = 100

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")]
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(console)


# ==================== CONFIGURATION ====================
@dataclass
class Config:
    target_dir: Optional[Path] = None
    auto_replace: bool = False          # Safe default: ask before overwriting
    use_trash: bool = True              # Try to use send2trash if available

    def __post_init__(self):
        self._send2trash = None
        if self.use_trash:
            try:
                import send2trash
                self._send2trash = send2trash
                logging.info("send2trash available – undo will use recycle bin.")
            except ImportError:
                logging.warning("send2trash not installed. Undo will use permanent deletion.")
                self.use_trash = False

    def send2trash(self, path: Path) -> bool:
        """Move path to trash/recycle bin. Returns True on success."""
        if self._send2trash:
            try:
                self._send2trash.send2trash(str(path))
                return True
            except Exception as e:
                logging.error(f"send2trash failed: {e}")
                return False
        return False


# ==================== SESSION CLASS – ENCAPSULATES GLOBAL STATE ====================
class ExporterSession:
    """Holds configuration, operation stack, and backup root for a single session."""
    def __init__(self, config: Config):
        self.config = config
        self.operation_stack: List[List[Tuple[Path, Path, bool, Optional[Path]]]] = []
        self.backup_root: Optional[Path] = None

    def get_backup_root(self) -> Path:
        if self.backup_root is None:
            self.backup_root = Path(tempfile.gettempdir()) / BACKUP_DIR_NAME
            self.backup_root.mkdir(exist_ok=True)
        return self.backup_root

    def push_transaction(self, transaction: List[Tuple[Path, Path, bool, Optional[Path]]]) -> None:
        self.operation_stack.append(transaction)

    def pop_transaction(self) -> Optional[List[Tuple[Path, Path, bool, Optional[Path]]]]:
        return self.operation_stack.pop() if self.operation_stack else None

    def get_active_backups(self) -> set:
        """Return set of all backup paths currently referenced in the undo stack."""
        active = set()
        for transaction in self.operation_stack:
            for (_, _, _, backup_path) in transaction:
                if backup_path and backup_path.exists():
                    active.add(backup_path)
        return active


# ==================== PATH PARSING ====================
def parse_paths_from_line(line: str) -> List[Path]:
    """Robustly split a line into existing paths using shlex (respects quotes)."""
    if not line.strip():
        return []
    try:
        tokens = shlex.split(line, posix=False)
    except ValueError as e:
        logging.warning(f"Could not parse line due to quoting error: {e}")
        logging.warning(f"Skipping malformed input: {line}")
        return []
    paths = []
    for t in tokens:
        p = Path(t.strip())
        if p.exists():
            paths.append(p)
        else:
            logging.warning(f"Ignored non-existent path: {t}")
    return paths

def parse_user_input_lines(lines: List[str]) -> List[Path]:
    """Collect paths from multiple input lines, deduplicate preserving order."""
    all_paths = []
    for line in lines:
        all_paths.extend(parse_paths_from_line(line))
    seen = set()
    unique = []
    for p in all_paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    duplicates = len(all_paths) - len(unique)
    if duplicates:
        logging.info(f"Ignored {duplicates} duplicate path(s).")
    return unique


# ==================== PROGRESS & COPY ====================
def get_total_bytes(path: Path) -> int:
    """Return total bytes of a file or all files in a folder (ignores symlinks)."""
    if path.is_file() and not path.is_symlink():
        return path.stat().st_size
    total = 0
    for f in path.rglob('*'):
        if f.is_file() and not f.is_symlink():
            total += f.stat().st_size
    return total

def format_bytes(b: int) -> str:
    """Human-readable bytes."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if b < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} TB"

def copy_with_progress(src: Path, dst: Path, total_bytes: int = None) -> bool:
    """Copy a single file with progress bar (bytes-based)."""
    if total_bytes is None:
        total_bytes = src.stat().st_size if not src.is_symlink() else 0
    if total_bytes == 0:
        if src.is_symlink():
            target = os.readlink(str(src))
            os.symlink(target, str(dst))
            print(f"\r📦 Progress: |{'█'*PROGRESS_BAR_LEN}| 100.0%", flush=True)
            return True
        dst.touch()
        shutil.copystat(src, dst)
        print(f"\r📦 Progress: |{'█'*PROGRESS_BAR_LEN}| 100.0%", flush=True)
        return True

    copied = 0
    try:
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                chunk = fsrc.read(CHUNK_SIZE)
                if not chunk:
                    break
                fdst.write(chunk)
                copied += len(chunk)
                percent = (copied / total_bytes) * 100
                filled = int(PROGRESS_BAR_LEN * copied // total_bytes)
                bar = '█' * filled + '░' * (PROGRESS_BAR_LEN - filled)
                print(f"\r📦 Progress: |{bar}| {percent:.1f}% ({format_bytes(copied)}/{format_bytes(total_bytes)})",
                      end='', flush=True)
        print()
        shutil.copystat(src, dst)
        return True
    except KeyboardInterrupt:
        if dst.exists():
            dst.unlink()
        print("\n⚠️ Copy interrupted by user. Partial file removed.")
        return False
    except Exception as e:
        logging.error(f"Copy failed: {e}")
        return False

def copy_folder_with_progress(src: Path, dst: Path) -> bool:
    """Copy folder with byte‑based progress bar, preserving symlinks."""
    total_bytes = get_total_bytes(src)
    copied_bytes = 0
    try:
        def progress_copy(src_item: str, dst_item: str):
            nonlocal copied_bytes
            src_p = Path(src_item)
            dst_p = Path(dst_item)

            if src_p.is_symlink():
                link_target = os.readlink(str(src_p))
                os.symlink(link_target, str(dst_p))
                percent = (copied_bytes / total_bytes) * 100 if total_bytes > 0 else 100.0
                percent = min(percent, 100.0)
                filled = int(PROGRESS_BAR_LEN * copied_bytes // total_bytes) if total_bytes > 0 else PROGRESS_BAR_LEN
                bar = '█' * filled + '░' * (PROGRESS_BAR_LEN - filled)
                print(f"\r📁 Folder progress: |{bar}| {percent:.1f}% ({format_bytes(copied_bytes)}/{format_bytes(total_bytes)})",
                      end='', flush=True)
                return

            if src_p.is_file():
                size = src_p.stat().st_size
                shutil.copy2(src_p, dst_p)
                copied_bytes += size
                percent = (copied_bytes / total_bytes) * 100 if total_bytes > 0 else 100.0
                percent = min(percent, 100.0)
                filled = int(PROGRESS_BAR_LEN * copied_bytes // total_bytes) if total_bytes > 0 else PROGRESS_BAR_LEN
                bar = '█' * filled + '░' * (PROGRESS_BAR_LEN - filled)
                print(f"\r📁 Folder progress: |{bar}| {percent:.1f}% ({format_bytes(copied_bytes)}/{format_bytes(total_bytes)})",
                      end='', flush=True)
            elif src_p.is_dir():
                dst_p.mkdir(parents=True, exist_ok=True)

        shutil.copytree(src, dst, copy_function=progress_copy, dirs_exist_ok=True, symlinks=True)
        print()
        return True
    except KeyboardInterrupt:
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        print("\n⚠️ Folder copy interrupted by user. Partial copy removed.")
        return False
    except Exception as e:
        logging.error(f"Folder copy failed: {e}")
        return False

def copy_symlink(src: Path, dst: Path) -> bool:
    """Copy a symlink preserving the link."""
    try:
        target = os.readlink(str(src))
        os.symlink(target, str(dst))
        logging.info(f"Copied symlink {src} -> {dst} (points to {target})")
        return True
    except Exception as e:
        logging.error(f"Failed to copy symlink {src}: {e}")
        return False


# ==================== SAFE COPY & UNDO (using session) ====================
def backup_if_exists(dest: Path, session: ExporterSession) -> Optional[Path]:
    """If dest exists, move it to backup folder. Returns backup path or None."""
    if not dest.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"{dest.name}.{timestamp}.backup"
    backup_dir = session.get_backup_root()
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / backup_name
    shutil.move(str(dest), str(backup_path))
    logging.info(f"Backed up existing item to {backup_path}")
    return backup_path

def restore_backup(backup_path: Path, original_dest: Path) -> bool:
    """Restore a backup to its original location. Assumes original_dest does not exist."""
    try:
        shutil.move(str(backup_path), str(original_dest))
        logging.info(f"Restored backup to {original_dest}")
        return True
    except Exception as e:
        logging.error(f"Restore failed: {e}")
        return False

def copy_single_item(src: Path, target_dir: Path, auto_replace: bool, session: ExporterSession) -> Optional[Tuple[Path, Path, bool, Optional[Path]]]:
    """
    Copy one file/folder to target.
    Returns (destination_path, source_path, was_overwrite, backup_path) on success, else None.
    """
    if not src.exists():
        logging.error(f"Source not found: {src}")
        return None

    if src.is_file() or src.is_symlink():
        dest = target_dir / src.name
        is_folder = False
    elif src.is_dir():
        dest = target_dir / src.name
        is_folder = True
    else:
        logging.error(f"Not a file/dir/symlink: {src}")
        return None

    was_overwrite = False
    backup_path = None
    backup_created = False

    def rollback():
        if backup_created and backup_path and backup_path.exists():
            if dest.exists():
                if dest.is_file() or dest.is_symlink():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(dest, ignore_errors=True)
            restore_backup(backup_path, dest)

    logging.info(f"Copying '{src.name}'...")
    success = False
    try:
        if dest.exists():
            if not auto_replace:
                answer = input(f"⚠️ '{dest.name}' already exists. Overwrite? (y/n): ").strip().lower()
                if answer != 'y':
                    logging.info(f"Skipped {src.name}")
                    return None
            backup_path = backup_if_exists(dest, session)
            backup_created = True
            was_overwrite = True

        if src.is_symlink():
            success = copy_symlink(src, dest)
        elif is_folder:
            success = copy_folder_with_progress(src, dest)
        else:
            total = get_total_bytes(src)
            success = copy_with_progress(src, dest, total_bytes=total)

        if not success:
            rollback()
            return None
    except (Exception, KeyboardInterrupt) as e:
        rollback()
        if isinstance(e, KeyboardInterrupt):
            raise
        raise

    if success:
        logging.info(f"Copied {src} -> {dest}")
        return (dest, src, was_overwrite, backup_path)
    return None

def copy_multiple_items(paths: List[Path], target_dir: Path, auto_replace: bool, session: ExporterSession) -> List[Tuple[Path, Path, bool, Optional[Path]]]:
    """Copy list of paths, returning list of successful entries. Also triggers backup cleanup."""
    successful = []
    for p in paths:
        try:
            entry = copy_single_item(p, target_dir, auto_replace, session)
            if entry:
                successful.append(entry)
        except KeyboardInterrupt:
            logging.info("\n⚠️ Copy interrupted – stopping further items.")
            break
    # Clean up old backups after every batch (keeps temp folder tidy)
    cleanup_old_backups(session)
    return successful

def undo_last_operation(session: ExporterSession):
    """Undo last copy transaction: delete or restore overwritten files."""
    transaction = session.pop_transaction()
    if transaction is None:
        logging.info("Nothing to undo.")
        return

    confirm = input("⚠️ Undo will remove the last copied files/folders. Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        logging.info("Undo cancelled.")
        # Push back the transaction we just popped
        session.push_transaction(transaction)
        return

    for (dest, src, was_overwrite, backup_path) in transaction:
        try:
            if was_overwrite and backup_path and backup_path.exists():
                if dest.exists():
                    if dest.is_file() or dest.is_symlink():
                        dest.unlink()
                    elif dest.is_dir():
                        shutil.rmtree(dest, ignore_errors=True)
                restore_backup(backup_path, dest)
            else:
                if dest.exists():
                    if session.config.use_trash and session.config.send2trash(dest):
                        logging.info(f"Moved to trash: {dest}")
                    else:
                        if dest.is_file() or dest.is_symlink():
                            dest.unlink()
                            logging.info(f"Deleted file: {dest}")
                        elif dest.is_dir():
                            shutil.rmtree(dest)
                            logging.info(f"Deleted folder: {dest}")
        except Exception as e:
            logging.error(f"Undo failed for {dest}: {e}")

    cleanup_old_backups(session)

def cleanup_old_backups(session: ExporterSession, keep: int = BACKUP_RETENTION_COUNT):
    """Remove stale backups older than retention count, preserving active undo backups."""
    backup_dir = session.get_backup_root()
    all_backups = list(backup_dir.glob("*.backup"))
    if not all_backups:
        return

    active_backups = session.get_active_backups()
    stale_backups = [b for b in all_backups if b not in active_backups]
    stale_backups.sort(key=lambda p: p.stat().st_mtime)

    if len(stale_backups) > keep:
        to_delete = stale_backups[:len(stale_backups) - keep]
        for b in to_delete:
            try:
                b.unlink()
            except Exception:
                pass


# ==================== TARGET DIRECTORY VALIDATION ====================
def validate_target_dir(path: Optional[Path]) -> Optional[Path]:
    """Return validated Path or None if invalid."""
    if path is None:
        path = Path.home() / "Desktop"
        if not path.exists():
            path = Path.home() / "OneDrive" / "Desktop"
    else:
        path = path.expanduser().resolve()
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created target directory: {path}")
        except Exception as e:
            logging.error(f"Cannot create target directory {path}: {e}")
            return None
    if not os.access(str(path), os.W_OK):
        logging.error(f"Target directory is not writable: {path}")
        return None
    return path


# ==================== SETTINGS MENU ====================
def change_settings(session: ExporterSession):
    print("\n--- Settings ---")
    print(f"1. Target directory: {session.config.target_dir or 'Desktop'}")
    print(f"2. Auto-replace (overwrite without asking): {'ON' if session.config.auto_replace else 'OFF'}")
    print(f"3. Use recycle bin for undo: {'ON' if session.config.use_trash else 'OFF'}")
    choice = input("Change? (1/2/3/0=cancel): ").strip()
    if choice == '1':
        new = input("New target path (blank for Desktop): ").strip()
        if new:
            new_path = Path(new).expanduser().resolve()
            if validate_target_dir(new_path):
                session.config.target_dir = new_path
                logging.info(f"Target updated to {session.config.target_dir}")
            else:
                logging.error("Invalid target directory, unchanged.")
        else:
            session.config.target_dir = None
            logging.info("Target set to Desktop.")
    elif choice == '2':
        session.config.auto_replace = not session.config.auto_replace
        logging.info(f"Auto-replace now {'ON' if session.config.auto_replace else 'OFF'}")
    elif choice == '3':
        if session.config.use_trash:
            session.config.use_trash = False
            session.config._send2trash = None
        else:
            try:
                import send2trash
                session.config.use_trash = True
                session.config._send2trash = send2trash
            except ImportError:
                logging.error("send2trash not installed. Cannot enable recycle bin.")
                return
        logging.info(f"Recycle bin undo {'ON' if session.config.use_trash else 'OFF'}")


# ==================== MAIN INTERACTIVE SHELL ====================
def interactive_shell():
    config_obj = Config()
    session = ExporterSession(config_obj)

    target = validate_target_dir(config_obj.target_dir)
    if target is None:
        logging.error("No valid target directory. Exiting.")
        return
    config_obj.target_dir = target

    while True:
        print("\n" + "="*50)
        print(f"📂 TARGET: {config_obj.target_dir}")
        print("   [1] Copy files/folders (any number, drag‑and‑drop or list)")
        print("   [2] Settings")
        print("   [3] Undo last copy")
        print("   [0] Exit")
        choice = input("Your choice: ").strip()

        if choice == '1':
            print("\n📂 Paste file/folder paths (drag‑and‑drop, one per line, or space‑separated).")
            print("   Type 'done' on a new line when finished.\n")
            lines = []
            while True:
                line = input("> ").strip()
                if line.lower() in ('done', ''):
                    break
                lines.append(line)
            if not lines:
                continue
            all_paths = parse_user_input_lines(lines)
            if not all_paths:
                continue
            print(f"\n📦 Copying {len(all_paths)} item(s)...")
            try:
                entries = copy_multiple_items(all_paths, config_obj.target_dir, config_obj.auto_replace, session)
                if entries:
                    session.push_transaction(entries)
                    logging.info(f"✅ Copied {len(entries)}/{len(all_paths)} items.")
                else:
                    logging.info("Nothing was copied.")
            except KeyboardInterrupt:
                logging.info("\n⚠️ Operation cancelled by user.")
                continue
        elif choice == '2':
            change_settings(session)
            new_target = validate_target_dir(session.config.target_dir)
            if new_target:
                session.config.target_dir = new_target
        elif choice == '3':
            undo_last_operation(session)
        elif choice == '0':
            logging.info("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice.")


if __name__ == "__main__":
    try:
        interactive_shell()
    except KeyboardInterrupt:
        logging.info("\nExporter terminated by user.")
        sys.exit(0)
