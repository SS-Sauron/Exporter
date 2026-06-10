#!/usr/bin/env python3
"""
Exporter – Safe, interactive file/folder copier with undo and progress bars.
Requires Python 3.10+.  Optional: pip install send2trash (recycle-bin undo).
"""

import argparse
import getpass
import logging
import os
import re as _re
import shlex
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

CHUNK_SIZE          = 8 * 1024 * 1024   # 8 MB – optimal for modern SSD transfers
PROGRESS_BAR_LEN    = 30
LOG_FILE            = Path.home() / ".exporter_log.txt"
MAX_LOG_BYTES       = 5 * 1024 * 1024   # 5 MB cap before rotation
LOG_BACKUP_COUNT    = 2
BACKUP_RETENTION    = 100           # stale backups kept per session dir

# ── Terminal UI ────────────────────────────────────────────────────────────────
#
# All colour and layout helpers live here.  The rest of the file only calls
# them for display — the transfer logic never reads these values.

_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

def _a(*codes: int) -> str:
    """Return an ANSI escape sequence, or '' when colour is disabled."""
    return f'\033[{";".join(str(c) for c in codes)}m' if _COLOR else ''

# ─ Styles ─────
RST  = _a(0);  BOLD = _a(1);  DIM = _a(2)

# ─ Colours ────
RED  = _a(31);  GRN  = _a(32);  YLW  = _a(33);  BLU  = _a(34)
MGN  = _a(35);  CYN  = _a(36);  GRY  = _a(90);  WHT  = _a(97)
BRED = _a(91);  BGRN = _a(92);  BYLW = _a(93);  BBLU = _a(94)
BMGN = _a(95);  BCYN = _a(96)

# ─ Semantic aliases ────────────────────────────────────────────────────────────
MUTED = GRY             # secondary / hint text
PATH  = BCYN            # file and directory paths
HEAD  = WHT + BOLD      # headings / labels
OK_C  = BGRN            # success
WRN_C = BYLW            # warning
ERR_C = BRED + BOLD     # error

_ANSI = _re.compile(r'\033\[[0-9;]*m')

def _vis(s: str) -> int:
    """Visible character count of a string (ANSI codes are invisible)."""
    return len(_ANSI.sub('', s))

# ─ Layout helpers ──────────────────────────────────────────────────────────────
_W = 56    # column width for rules and right-aligned metadata

def _rule(label: str = '') -> str:
    """Horizontal rule, optionally wrapping a centred label."""
    if not label:
        return f'  {MUTED}{"─" * _W}{RST}'
    gap   = _W - _vis(label) - 2
    left  = max(0, gap // 2)
    right = max(0, gap - left)
    return f'  {MUTED}{"─" * left} {RST}{label}{MUTED} {"─" * right}{RST}'

def _rpad(left: str, right: str, width: int = _W) -> str:
    """Pad between two strings so their visible widths sum to `width`."""
    gap = max(1, width + 2 - _vis(left) - _vis(right))
    return f'{left}{" " * gap}{right}'

# ─ Semantic print helpers ──────────────────────────────────────────────────────
def _ok(msg: str)   -> None: print(f'  {OK_C}✓{RST}  {msg}')
def _warn(msg: str) -> None: print(f'  {WRN_C}!{RST}  {WRN_C}{msg}{RST}')
def _err(msg: str)  -> None: print(f'  {ERR_C}✗{RST}  {ERR_C}{msg}{RST}')

def _prompt(label: str = '') -> str:
    """Styled ›-prompt. Returns the stripped response."""
    arrow = f'{BCYN}›{RST}'
    if label:
        return input(f'  {MUTED}{label}{RST}  {arrow} ').strip()
    return input(f'  {arrow} ').strip()

def _confirm(question: str) -> bool:
    """Styled yes/no prompt. Returns True for 'y'."""
    ans = _prompt(f'{question}  {MUTED}[y/n]{RST}')
    return ans.lower() == 'y'



# ── Logging ────────────────────────────────────────────────────────────────────

class _ColourFormatter(logging.Formatter):
    """Console formatter: icon + ANSI colour per level, no timestamps."""
    _MAP = {
        logging.DEBUG:    (MUTED, '·'),
        logging.INFO:     (MUTED, '·'),
        logging.WARNING:  (WRN_C, '!'),
        logging.ERROR:    (ERR_C, '✗'),
        logging.CRITICAL: (ERR_C, '✗'),
    }
    def format(self, record: logging.LogRecord) -> str:
        colour, icon = self._MAP.get(record.levelno, (MUTED, '·'))
        return f'  {colour}{icon}{RST}  {colour}{record.getMessage()}{RST}'


def _setup_logging() -> None:
    """Configure root logger. Guards against duplicate handlers on reimport."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Rotating file handler — plain text, no ANSI codes in the log file.
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        fh = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_LOG_BYTES,
            backupCount=LOG_BACKUP_COUNT, encoding="utf-8",
        )
        fh.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root.addHandler(fh)
    # Console handler — coloured output, no timestamps.
    has_console = any(
        isinstance(h, logging.StreamHandler)
        and not isinstance(h, RotatingFileHandler)
        for h in root.handlers
    )
    if not has_console:
        ch = logging.StreamHandler()
        ch.setFormatter(_ColourFormatter())
        root.addHandler(ch)


_setup_logging()

# ── Named type for a reversible copy operation ─────────────────────────────────

@dataclass
class OperationRecord:
    """Represents one successful copy that can later be undone."""
    dest:          Path
    src:           Path
    was_overwrite: bool
    backup_path:   Path | None

    def describe(self) -> str:
        if self.was_overwrite and self.backup_path:
            return f"  restore overwrite : {self.dest}  (backup exists)"
        return f"  delete            : {self.dest}"

# ── Configuration ──────────────────────────────────────────────────────────────

class Config:
    """
    Runtime configuration. Use Config.create() – not the constructor directly –
    so that optional dependency loading (send2trash) stays out of __init__.
    """

    def __init__(
        self,
        target_dir:   Path | None = None,
        auto_replace: bool = False,
        use_trash:    bool = True,
    ) -> None:
        self.target_dir   = target_dir
        self.auto_replace = auto_replace
        self.use_trash    = use_trash
        self._send2trash  = None

    @classmethod
    def create(
        cls,
        target_dir:   Path | None = None,
        auto_replace: bool = False,
        use_trash:    bool = True,
    ) -> "Config":
        """Factory: construct Config then attempt to load send2trash."""
        cfg = cls(target_dir=target_dir, auto_replace=auto_replace, use_trash=use_trash)
        if use_trash:
            cfg.enable_trash(quiet=False)
        return cfg

    def enable_trash(self, quiet: bool = False) -> bool:
        """Try to activate recycle-bin undo. Returns True on success."""
        try:
            import send2trash as _s2t
            self._send2trash = _s2t
            self.use_trash = True
            if not quiet:
                logging.info("send2trash loaded – undo will use recycle bin.")
            return True
        except ImportError:
            self.use_trash = False
            if not quiet:
                logging.warning(
                    "send2trash not installed. Undo will permanently delete. "
                    "Run: pip install send2trash"
                )
            return False

    def disable_trash(self) -> None:
        self.use_trash   = False
        self._send2trash = None

    def send_to_trash(self, path: Path) -> bool:
        """Move path to the OS recycle bin. Returns True on success."""
        if self._send2trash:
            try:
                self._send2trash.send2trash(str(path))
                return True
            except Exception as exc:
                logging.error(f"send2trash failed for {path.name}: {exc}")
        return False

# ── Session (state container) ──────────────────────────────────────────────────

class ExporterSession:
    """Holds config, the undo stack, and the per-session backup directory."""

    def __init__(self, config: Config) -> None:
        self.config           = config
        self.operation_stack: list[list[OperationRecord]] = []
        self._backup_root:    Path | None = None

    # Backup root ──────────────────────────────────────────────────────────────

    def get_backup_root(self) -> Path:
        """
        Return (lazily creating) the backup directory.
        Scoped to the current OS user to prevent TOCTOU collisions between
        users sharing a system temp directory.
        """
        if self._backup_root is None:
            try:
                user = getpass.getuser()
            except (KeyError, OSError):
                user = str(os.getuid()) if hasattr(os, "getuid") else "unknown"
            root = Path(tempfile.gettempdir()) / f"exporter_{user}"
            root.mkdir(mode=0o700, exist_ok=True)
            self._backup_root = root
        return self._backup_root

    # Stack helpers ────────────────────────────────────────────────────────────

    def push_transaction(self, records: list[OperationRecord]) -> None:
        self.operation_stack.append(records)

    def pop_transaction(self) -> list[OperationRecord] | None:
        return self.operation_stack.pop() if self.operation_stack else None

    def peek_transaction(self) -> list[OperationRecord] | None:
        return self.operation_stack[-1] if self.operation_stack else None

    def undo_depth(self) -> int:
        return len(self.operation_stack)

    def get_active_backups(self) -> set[Path]:
        """All backup paths currently referenced by the undo stack."""
        active: set[Path] = set()
        for txn in self.operation_stack:
            for rec in txn:
                if rec.backup_path and rec.backup_path.exists():
                    active.add(rec.backup_path)
        return active

# ── Path parsing ───────────────────────────────────────────────────────────────

def _unquote(token: str) -> str:
    """Strip a single layer of matching outer quotes from a shlex token."""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def parse_paths_from_line(line: str) -> list[Path]:
    """
    Split one input line into existing Paths using shlex.
    posix=False keeps backslashes as literals, which is required for
    Windows-style paths (C:\\Users\\foo). Outer quotes are stripped by
    _unquote so quoted paths with spaces still work on all platforms.
    """
    if not line.strip():
        return []
    try:
        tokens = [_unquote(t) for t in shlex.split(line, posix=False)]
    except ValueError as exc:
        logging.warning(f"Ignoring malformed input ({exc}): {line!r}")
        return []

    paths: list[Path] = []
    for tok in tokens:
        p = Path(tok)
        if p.exists() or p.is_symlink():     # include dangling symlinks
            paths.append(p)
        else:
            logging.warning(f"Ignored non-existent path: {tok!r}")
    return paths


def parse_user_input_lines(lines: list[str]) -> list[Path]:
    """Flatten multiple input lines into a deduplicated, ordered path list."""
    all_paths: list[Path] = []
    for line in lines:
        all_paths.extend(parse_paths_from_line(line))

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in all_paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    dupes = len(all_paths) - len(unique)
    if dupes:
        logging.info(f"Ignored {dupes} duplicate path(s).")
    return unique

# ── Shared utilities ───────────────────────────────────────────────────────────

def get_total_bytes(path: Path) -> int:
    """
    Recursively sum file sizes using an iterative os.scandir traversal.

    Advantages over Path.rglob():
    - DirEntry.stat() reuses the kernel buffer populated by os.scandir on
      many OS/FS combinations (Windows always; Linux/macOS for d_type hits).
    - No Path object is created per entry – only bare strings are kept on
      the stack, reducing per-iteration allocation.
    - OSError on unreadable sub-directories is caught locally so a single
      bad entry never aborts the entire scan.
    """
    if path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    stack: list[str] = [str(path)]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError:
                        pass  # skip unreadable entries
        except OSError:
            pass  # skip unreadable directories
    return total


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def _render_bar(copied: int, total: int, label: str = "copying") -> str:
    """Colour-coded progress bar (\\r prefix so it overwrites the current line)."""
    if total > 0:
        pct    = min(copied / total * 100, 100.0)
        filled = min(int(PROGRESS_BAR_LEN * copied // total), PROGRESS_BAR_LEN)
    else:
        pct, filled = 100.0, PROGRESS_BAR_LEN
    empty = PROGRESS_BAR_LEN - filled
    bar   = f'{BGRN}{"█" * filled}{RST}{MUTED}{"░" * empty}{RST}'
    pct_s = f'{WHT}{pct:.0f}%{RST}'
    szs   = f'{BCYN}{format_bytes(copied)}{MUTED}/{RST}{BCYN}{format_bytes(total)}{RST}'
    return f'\r  {MUTED}{label}{RST}  {bar}  {pct_s}  {szs}'


def _remove_path(path: Path) -> None:
    """
    Remove a file, directory, or symlink (including dangling ones).
    Silently ignores already-missing paths.
    """
    try:
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except Exception as exc:
        logging.error(f"Could not remove {path}: {exc}")

# ── File copy routines ─────────────────────────────────────────────────────────

def copy_with_progress(src: Path, dst: Path, total_bytes: int | None = None) -> bool:
    """Copy a single regular file with a live byte-count progress bar."""
    if total_bytes is None:
        total_bytes = src.stat().st_size if not src.is_symlink() else 0

    if total_bytes == 0:
        dst.touch()
        shutil.copystat(src, dst)
        bar = f'{BGRN}{"█" * PROGRESS_BAR_LEN}{RST}'
        print(f'  {MUTED}copying{RST}  {bar}  {WHT}100%{RST}')
        return True

    copied = 0
    try:
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            while chunk := fsrc.read(CHUNK_SIZE):
                fdst.write(chunk)
                copied += len(chunk)
                print(_render_bar(copied, total_bytes, "copying"), end="", flush=True)
        print()
        try:
            shutil.copystat(src, dst)
        except OSError as exc:
            logging.warning(
                f"Could not copy metadata for '{dst.name}': {exc} "
                "(file content was copied successfully)"
            )
        return True
    except KeyboardInterrupt:
        dst.unlink(missing_ok=True)
        print(f'\n  {WRN_C}!{RST}  Copy interrupted — partial file removed.')
        return False
    except Exception as exc:
        logging.error(f"Copy failed for {src.name}: {exc}")
        dst.unlink(missing_ok=True)
        return False


def copy_folder_with_progress(src: Path, dst: Path) -> bool:
    """
    Copy a directory tree with a byte-based progress bar, preserving symlinks.

    The function performs a single os.scandir pre-scan to build a size lookup
    table (dict[src_path → bytes]).  The shutil.copytree callback then reads
    pre-computed sizes instead of issuing a second stat() call per file,
    halving the number of filesystem round-trips for the sizing phase.

    A 'calculating size…' indicator is shown immediately so the terminal
    never appears frozen while scanning a large directory tree.
    """
    # ── Pre-scan: collect sizes and signal progress ────────────────────────────
    print(f'  {MUTED}calculating size...{RST}', end='', flush=True)
    file_sizes: dict[str, int] = {}
    total_bytes = 0
    stack: list[str] = [str(src)]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat(follow_symlinks=False).st_size
                            file_sizes[entry.path] = size
                            total_bytes += size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError:
                        pass
        except OSError:
            pass

    # Show the initial bar state, which overwrites 'calculating size...' via \r.
    # For an empty folder total_bytes==0 renders a completed 100% bar immediately.
    print(_render_bar(0, total_bytes, "folder "), end='', flush=True)

    copied_bytes = 0

    def _copy_fn(src_str: str, dst_str: str) -> None:
        """Callback for shutil.copytree — only ever called for regular files.
        copytree(symlinks=True) handles symlinks itself via os.symlink before
        this callback is invoked, so no symlink check is needed here.
        Size is retrieved from the pre-scan dict; no extra stat() call."""
        nonlocal copied_bytes
        size = file_sizes.get(src_str, 0)
        shutil.copy2(src_str, dst_str)
        copied_bytes += size
        print(_render_bar(copied_bytes, total_bytes, "folder "), end="", flush=True)

    try:
        shutil.copytree(src, dst, copy_function=_copy_fn, dirs_exist_ok=True, symlinks=True)
        print()
        return True
    except KeyboardInterrupt:
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        print(f'\n  {WRN_C}!{RST}  Folder copy interrupted — partial copy removed.')
        return False
    except Exception as exc:
        logging.error(f"Folder copy failed for {src.name}: {exc}")
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        return False


def copy_symlink(src: Path, dst: Path) -> bool:
    """Reproduce a symlink at dst pointing to the same target as src."""
    try:
        os.symlink(os.readlink(str(src)), str(dst))
        logging.info(f"Copied symlink: {src} -> {dst}")
        return True
    except Exception as exc:
        logging.error(f"Failed to copy symlink {src.name}: {exc}")
        return False

# ── Backup & restore ───────────────────────────────────────────────────────────

def backup_if_exists(dest: Path, session: ExporterSession) -> Path | None:
    """
    If dest exists (or is a dangling symlink), move it into the session backup
    directory. Returns the backup path on success, or None on failure / no-op.
    """
    if not dest.exists() and not dest.is_symlink():
        return None

    size_str = format_bytes(get_total_bytes(dest))
    print(
        f'  {MUTED}backing up{RST}  {PATH}{dest.name}{RST}'
        f'  {MUTED}({size_str}){RST}',
        end='', flush=True,
    )

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = session.get_backup_root() / f"{dest.name}.{timestamp}.backup"
    try:
        shutil.move(str(dest), str(backup_path))
        print(f'  {OK_C}done{RST}')
        logging.info(f"Backed up '{dest.name}' -> {backup_path}")
        return backup_path
    except Exception as exc:
        print()
        logging.error(f"Backup failed for '{dest.name}': {exc}")
        return None


def restore_backup(backup_path: Path, dest: Path) -> bool:
    """Move a backup back to its original location."""
    try:
        shutil.move(str(backup_path), str(dest))
        logging.info(f"Restored '{dest.name}' from backup.")
        return True
    except Exception as exc:
        logging.error(f"Restore failed ({backup_path} -> {dest}): {exc}")
        return False

# ── Post-copy size check ───────────────────────────────────────────────────────

def warn_if_size_mismatch(src: Path, dest: Path) -> None:
    """
    Compare source and destination sizes and log a warning if they differ.
    Skipped for symlinks (no byte content to compare).
    This is a side-effect-only function; the copy is kept regardless.
    """
    if src.is_symlink():
        return
    src_size  = get_total_bytes(src)
    dest_size = get_total_bytes(dest)
    if src_size != dest_size:
        logging.warning(
            f"Size mismatch for '{dest.name}': "
            f"expected {format_bytes(src_size)}, got {format_bytes(dest_size)}. "
            "The copy may be incomplete."
        )

# ── Copy orchestration ─────────────────────────────────────────────────────────

def copy_single_item(
    src:          Path,
    target_dir:   Path,
    auto_replace: bool,
    session:      ExporterSession,
) -> OperationRecord | None:
    """
    Copy one file, directory, or symlink into target_dir.
    Returns an OperationRecord on success, or None if skipped or failed.

    Safety contract:
    - An existing destination is always backed up before being overwritten.
    - If the backup itself fails, the copy is aborted to prevent data loss.
    - A rollback removes any partial destination and restores the backup
      if an error occurs mid-copy.
    """
    if not src.exists() and not src.is_symlink():
        logging.error(f"Source not found: {src}")
        return None

    dest          = target_dir / src.name
    was_overwrite = False
    backup_path:  Path | None = None

    # ── Ask / back up if destination already exists ────────────────────────
    if dest.exists() or dest.is_symlink():
        if not auto_replace:
            print(f'\n  {WRN_C}!{RST}  {PATH}{dest.name}{RST} already exists.')
            if not _confirm('Overwrite?'):
                logging.info(f"Skipped: {src.name}")
                return None

        backup_path = backup_if_exists(dest, session)
        if backup_path is None:
            # Backup attempt returned None but dest still exists → backup failed.
            if dest.exists() or dest.is_symlink():
                logging.error(
                    f"Cannot back up existing '{dest.name}'. "
                    "Skipping to prevent data loss."
                )
                return None
        was_overwrite = True

    # ── Rollback helper ────────────────────────────────────────────────────
    def rollback() -> None:
        _remove_path(dest)
        if backup_path and backup_path.exists():
            restore_backup(backup_path, dest)

    # ── Perform the copy ───────────────────────────────────────────────────
    logging.info(f"Copying '{src.name}' ...")
    success = False
    try:
        if src.is_symlink():
            success = copy_symlink(src, dest)
        elif src.is_dir():
            success = copy_folder_with_progress(src, dest)
        else:
            success = copy_with_progress(src, dest, total_bytes=get_total_bytes(src))
    except KeyboardInterrupt:
        rollback()
        raise
    except Exception as exc:
        logging.error(f"Unexpected error copying '{src.name}': {exc}")
        rollback()
        return None

    if not success:
        rollback()
        return None

    # ── Post-copy size check (side-effect only; copy is kept regardless) ───────
    warn_if_size_mismatch(src, dest)

    logging.info(f"Copied: {src} -> {dest}")
    return OperationRecord(
        dest=dest, src=src,
        was_overwrite=was_overwrite, backup_path=backup_path,
    )


def copy_multiple_items(
    paths:        list[Path],
    target_dir:   Path,
    auto_replace: bool,
    session:      ExporterSession,
) -> list[OperationRecord]:
    """Copy a list of paths; return successful OperationRecords."""
    records: list[OperationRecord] = []
    for p in paths:
        try:
            record = copy_single_item(p, target_dir, auto_replace, session)
            if record:
                records.append(record)
        except KeyboardInterrupt:
            logging.info("\n  Copy interrupted – no further items processed.")
            break
    cleanup_old_backups(session)
    return records

# ── Undo ───────────────────────────────────────────────────────────────────────

def undo_last_operation(session: ExporterSession) -> None:
    """Reverse the most recent copy transaction after showing a preview."""
    transaction = session.pop_transaction()
    if transaction is None:
        print()
        _warn('Nothing to undo.')
        return

    n = len(transaction)
    print()
    print(_rule(f'{HEAD}Undo preview{RST}  {MUTED}–  {n} item{"s" if n != 1 else ""}{RST}'))
    print()
    for rec in transaction:
        if rec.was_overwrite and rec.backup_path:
            icon, verb, note = f'{BYLW}↩{RST}', 'restore', f'  {MUTED}(backup available){RST}'
        else:
            icon, verb, note = f'{BRED}✗{RST}', 'delete ', ''
        print(f'  {icon}  {MUTED}{verb}{RST}  {PATH}{rec.dest.name}{RST}{note}')
    print()
    print(_rule())
    print()

    if not _confirm('Proceed with undo?'):
        session.push_transaction(transaction)
        logging.info("Undo cancelled.")
        return

    for rec in transaction:
        try:
            if rec.was_overwrite and rec.backup_path:
                if rec.backup_path.exists():
                    _remove_path(rec.dest)
                    restore_backup(rec.backup_path, rec.dest)
                else:
                    # Backup was deleted (e.g. by cleanup or external process).
                    # Refuse to delete dest blindly — that would destroy the only
                    # remaining copy with no way to recover.
                    logging.warning(
                        f"Backup for '{rec.dest.name}' is missing from disk. "
                        "Skipping undo for this item to prevent data loss. "
                        f"Backup was expected at: {rec.backup_path}"
                    )
                    continue
            elif rec.dest.exists() or rec.dest.is_symlink():
                if session.config.use_trash and session.config.send_to_trash(rec.dest):
                    logging.info(f"Sent to trash: {rec.dest}")
                else:
                    _remove_path(rec.dest)
                    logging.info(f"Deleted: {rec.dest}")
        except Exception as exc:
            logging.error(f"Undo failed for '{rec.dest.name}': {exc}")

    cleanup_old_backups(session)
    print()
    _ok('Undo complete.')

# ── Backup maintenance ─────────────────────────────────────────────────────────

def cleanup_old_backups(session: ExporterSession, keep: int = BACKUP_RETENTION) -> None:
    """
    Remove stale backup entries exceeding the retention count.
    Backups still referenced by the undo stack are never touched.
    Guards against FileNotFoundError from concurrent external deletions.
    """
    backup_dir = session.get_backup_root()
    all_entries = list(backup_dir.glob("*.backup"))
    if not all_entries:
        return

    active = session.get_active_backups()
    stale  = [b for b in all_entries if b not in active]

    def _safe_mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    stale.sort(key=_safe_mtime)           # oldest first

    if len(stale) > keep:
        for entry in stale[: len(stale) - keep]:
            try:
                _remove_path(entry)
            except Exception:
                pass

# ── Target directory validation ────────────────────────────────────────────────

def validate_target_dir(path: Path | None) -> Path | None:
    """Resolve, create-if-missing, and write-check the target directory."""
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
        except Exception as exc:
            logging.error(f"Cannot create target directory {path}: {exc}")
            return None

    if not os.access(str(path), os.W_OK):
        logging.error(f"Target directory is not writable: {path}")
        return None

    return path

# ── Settings menu ──────────────────────────────────────────────────────────────

def change_settings(session: ExporterSession) -> None:
    """
    Interactive settings loop. Stays open until the user presses 0.
    Validation happens here; no re-validation needed in the caller.
    """
    while True:
        td_raw = str(session.config.target_dir or 'Desktop (default)')
        if len(td_raw) > 42:
            td_raw = '…' + td_raw[-41:]
        td = f'{PATH}{td_raw}{RST}'
        ar = f'{OK_C}ON{RST}'  if session.config.auto_replace else f'{MUTED}OFF{RST}'
        tr = f'{OK_C}ON{RST}'  if session.config.use_trash    else f'{MUTED}OFF{RST}'

        print()
        print(_rule(f'{HEAD}Settings{RST}'))
        print()
        print(f'  {BOLD}1{RST}   Target directory  {MUTED}·{RST}  {td}')
        print(f'  {BOLD}2{RST}   Auto-replace      {MUTED}·{RST}  {ar}')
        print(f'  {BOLD}3{RST}   Recycle-bin undo  {MUTED}·{RST}  {tr}')
        print()
        print(f'  {MUTED}0   Back{RST}')
        print()

        match _prompt('Change?'):
            case "0":
                break

            case "1":
                raw      = _prompt('New target path  (blank = Desktop default)')
                new_path = Path(raw).expanduser().resolve() if raw else None
                validated = validate_target_dir(new_path)
                if validated:
                    session.config.target_dir = validated
                    logging.info(f"Target directory set to: {validated}")
                else:
                    _warn('Invalid or unwritable path — target unchanged.')

            case "2":
                session.config.auto_replace = not session.config.auto_replace
                logging.info(f"Auto-replace: {'ON' if session.config.auto_replace else 'OFF'}")

            case "3":
                if session.config.use_trash:
                    session.config.disable_trash()
                    logging.info("Recycle-bin undo: OFF")
                else:
                    if not session.config.enable_trash():
                        _warn('Install send2trash first:  pip install send2trash')

            case _:
                _warn('Invalid choice.')

# ── Undo-stack viewer ──────────────────────────────────────────────────────────

def view_undo_stack(session: ExporterSession) -> None:
    """Display all transactions in the undo stack, newest first."""
    print()
    if not session.operation_stack:
        _warn('Undo stack is empty.')
        return

    depth = session.undo_depth()
    print(_rule(
        f'{HEAD}Undo stack{RST}  '
        f'{MUTED}–  {depth} transaction{"s" if depth != 1 else ""}, newest first{RST}'
    ))
    for idx, txn in enumerate(reversed(session.operation_stack), start=1):
        print()
        print(f'  {BOLD}[{idx}]{RST}  {MUTED}{len(txn)} item{"s" if len(txn) != 1 else ""}{RST}')
        for rec in txn:
            tag = f'{BYLW}[ow]{RST}' if rec.was_overwrite else f'{MUTED}[new]{RST}'
            name = f'{PATH}{rec.dest.name}{RST}'
            src  = f'{MUTED}{rec.src}{RST}'
            print(f'       {tag}  {name}  {MUTED}←{RST}  {src}')
    print()

# ── CLI argument parsing ───────────────────────────────────────────────────────

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="exporter",
        description="Safe interactive file/folder copier with undo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python exporter.py\n"
            "  python exporter.py --target ~/Exports --auto-replace\n"
            "  python exporter.py --target /tmp/out --no-trash\n"
        ),
    )
    p.add_argument(
        "--target", "-t", metavar="DIR",
        help="Destination directory (default: Desktop)",
    )
    p.add_argument(
        "--auto-replace", "-y", action="store_true", default=False,
        help="Overwrite existing files without asking.",
    )
    p.add_argument(
        "--no-trash", action="store_true", default=False,
        help="Use permanent deletion for undo instead of the recycle bin.",
    )
    return p

# ── Input collection helper ────────────────────────────────────────────────────

def _collect_paths_interactively() -> list[Path]:
    """
    Prompt the user to paste paths line by line.
    Terminates only on the explicit keyword 'done' (not on blank Enter),
    so accidental Enter key-presses don't truncate the input session.
    """
    print()
    print(_rule(f'{HEAD}Add files / folders{RST}'))
    print(
        f'  {MUTED}Drag-and-drop or paste paths one per line.'
        f'  Type {RST}{BOLD}done{RST}{MUTED} when finished.{RST}'
    )
    print()
    lines: list[str] = []
    while True:
        try:
            line = input(f'  {BCYN}›{RST} ').strip()
        except EOFError:
            break
        if line.lower() == "done":
            break
        if line:
            lines.append(line)
        # Blank Enter is intentionally ignored – keeps the session open.

    return parse_user_input_lines(lines)

# ── Copy action ────────────────────────────────────────────────────────────────

def _do_copy(session: ExporterSession) -> None:
    """Collect paths, run the copy batch, push a transaction onto the stack."""
    paths = _collect_paths_interactively()
    if not paths:
        _warn('No valid paths provided.')
        return

    target = session.config.target_dir
    n      = len(paths)
    print()
    print(_rule())
    print(
        f'  {MUTED}copying {n} item{"s" if n != 1 else ""} to{RST}  '
        f'{PATH}{target}{RST}'
    )
    print()

    try:
        records = copy_multiple_items(
            paths, target, session.config.auto_replace, session,
        )
    except KeyboardInterrupt:
        print()
        _warn('Operation cancelled.')
        return

    print()
    if records:
        session.push_transaction(records)
        skipped = len(paths) - len(records)
        skip_s  = f'  {MUTED}({skipped} skipped){RST}' if skipped else ''
        _ok(
            f'Copied {BOLD}{len(records)}{RST} of {BOLD}{n}{RST}'
            f'{skip_s}  {MUTED}·{RST}  use {BOLD}[3]{RST} to undo'
        )
    else:
        _warn('Nothing was copied.')

# ── Main interactive shell ─────────────────────────────────────────────────────

def interactive_shell(args: argparse.Namespace) -> None:
    initial_target = (
        Path(args.target).expanduser().resolve() if args.target else None
    )
    config = Config.create(
        target_dir=initial_target,
        auto_replace=args.auto_replace,
        use_trash=not args.no_trash,
    )

    target = validate_target_dir(config.target_dir)
    if target is None:
        logging.error("No valid target directory. Exiting.")
        sys.exit(1)
    config.target_dir = target

    session = ExporterSession(config)

    # ── One-time welcome ───────────────────────────────────────────────────────
    print()
    print(f'  {HEAD}exporter{RST}  {MUTED}safe file copier with undo{RST}')

    while True:
        depth = session.undo_depth()

        path_s = str(config.target_dir)
        if len(path_s) > 46:
            path_s = '…' + path_s[-45:]

        undo_rhs = (
            f'{MUTED}{depth} step{"s" if depth != 1 else ""} available{RST}'
            if depth else f'{MUTED}nothing to undo{RST}'
        )
        undo_row = _rpad(
            f'  {BOLD}3{RST}  Undo last copy',
            undo_rhs,
        )

        print()
        print(f'  {MUTED}{"─" * _W}{RST}')
        print(f'  {MUTED}›{RST}  {PATH}{path_s}{RST}')
        print(f'  {MUTED}{"─" * _W}{RST}')
        print()
        print(f'  {BOLD}1{RST}  Copy files / folders')
        print(f'  {BOLD}2{RST}  Settings')
        print(undo_row)
        print(f'  {BOLD}4{RST}  View undo stack')
        print()
        print(f'  {MUTED}0  Exit{RST}')
        print()

        match _prompt():
            case "1": _do_copy(session)
            case "2": change_settings(session)
            case "3": undo_last_operation(session)
            case "4": view_undo_stack(session)
            case "0":
                print()
                _ok('Goodbye!')
                break
            case _:
                _warn('Invalid choice.')

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        interactive_shell(_build_arg_parser().parse_args())
    except KeyboardInterrupt:
        logging.info("\nExporter terminated by user.")
        sys.exit(0)
