"""Makes the packaged InventoryManager.exe self-installing.

Double-clicking the exe wherever it currently sits (Downloads, a USB
drive, the PyInstaller dist folder) should behave like running a real
Windows installer the first time: copy itself into a proper per-user
install location, register in Settings > Apps / Control Panel > Programs
and Features, add a Start Menu shortcut (so Windows Search finds it), and
launch from the installed copy. Every launch after that just runs the app
normally, since the registry entry created here is what marks it
"installed".

Uses only the standard library (winreg, subprocess + PowerShell's built-in
WScript.Shell COM object for the .lnk file) rather than adding a
dependency like pywin32 for this alone.
"""

import os
import shutil
import subprocess
import sys
import traceback
import winreg
from pathlib import Path

_DETACHED_FLAGS = (
    getattr(subprocess, "DETACHED_PROCESS", 0)
    | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
)


def _log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA", str(Path.home()))
    return Path(base) / "OfflineInventory" / "self_install.log"


def _log_exception(context: str) -> None:
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {context} ---\n")
            f.write(traceback.format_exc())
    except OSError:
        pass  # logging is best-effort; must never itself crash startup

APP_NAME = "Offline Inventory Management System"
APP_PUBLISHER = "Offline Inventory"
APP_VERSION = "1.0.0"
EXE_NAME = "InventoryManager.exe"

# Matches installer.iss's AppId, so a machine that has used either the
# Inno Setup installer or this self-install path (or both, over time)
# converges on one Control Panel entry instead of two.
UNINSTALL_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    r"\{B6C6D9E1-6F2E-4B9A-9C7D-6B6F0B1B4A9E}_is1"
)

UNINSTALL_FLAG = "--uninstall"


def install_dir() -> Path:
    import os

    base = os.environ.get("LOCALAPPDATA", str(Path.home()))
    return Path(base) / "Programs" / APP_NAME


def _current_app_dir() -> Path:
    """The folder the running exe lives in (PyInstaller onedir layout)."""
    return Path(sys.executable).resolve().parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def is_installed(key_path: str = UNINSTALL_KEY) -> bool:
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        return True
    except FileNotFoundError:
        return False


def _start_menu_programs_dir() -> Path:
    # APPDATA is the authoritative source for this (works with redirected
    # profiles); Path.home() / "AppData" / "Roaming" assumes a layout that
    # is not always accurate.
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def _create_start_menu_shortcut(target_exe: Path) -> None:
    start_menu = _start_menu_programs_dir()
    start_menu.mkdir(parents=True, exist_ok=True)
    shortcut_path = start_menu / f"{APP_NAME}.lnk"
    script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$shortcut.TargetPath = '{target_exe}'
$shortcut.WorkingDirectory = '{target_exe.parent}'
$shortcut.Save()
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        timeout=30,
        text=True,
    )
    if result.returncode != 0 or not shortcut_path.exists():
        try:
            path = _log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write("\n--- _create_start_menu_shortcut failed ---\n")
                f.write(f"returncode={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}\n")
        except OSError:
            pass


def _remove_start_menu_shortcut() -> None:
    (_start_menu_programs_dir() / f"{APP_NAME}.lnk").unlink(missing_ok=True)


def _register_uninstall_entry(installed_exe: Path, key_path: str = UNINSTALL_KEY) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(installed_exe))
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(installed_exe.parent))
        winreg.SetValueEx(
            key, "UninstallString", 0, winreg.REG_SZ, f'"{installed_exe}" {UNINSTALL_FLAG}'
        )
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


def _remove_uninstall_entry(key_path: str = UNINSTALL_KEY) -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except FileNotFoundError:
        pass


def perform_self_install() -> bool:
    """Copies the running app to the install folder (if not already there),
    registers it, adds a shortcut, then relaunches from the installed copy
    and exits this process. A no-op beyond re-registering if somehow
    already running from the install folder with a missing registry entry.

    Self-install is a convenience, not something that should ever be able
    to crash the app: any failure is logged to
    %LOCALAPPDATA%\\OfflineInventory\\self_install.log and swallowed, and
    this returns False so the caller just continues running normally
    (as a portable app) from wherever it currently is. Returns True only
    when it exits the process itself after relaunching.
    """
    try:
        current_dir = _current_app_dir()
        target_dir = install_dir()
        same_location = current_dir == target_dir

        if not same_location:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(current_dir, target_dir, dirs_exist_ok=True)

        installed_exe = target_dir / EXE_NAME
        _create_start_menu_shortcut(installed_exe)
        _register_uninstall_entry(installed_exe)

        if not same_location:
            # No creationflags here: DETACHED_PROCESS combined with a
            # windowed (console=False) PyInstaller bootloader exe causes
            # the relaunched child to exit immediately instead of running
            # - confirmed by testing, though GUI-subsystem processes don't
            # attach to a console anyway, so the default (inherit) is both
            # simpler and the one that actually works here.
            subprocess.Popen([str(installed_exe)], cwd=str(target_dir))
            sys.exit(0)
        return False
    except SystemExit:
        raise
    except Exception:
        _log_exception("perform_self_install")
        return False


def perform_uninstall() -> None:
    """Removes the shortcut and registry entry immediately, then schedules
    deletion of the install folder a couple seconds after this process
    exits (a running exe cannot delete the file backing itself)."""
    try:
        _remove_start_menu_shortcut()
        _remove_uninstall_entry()

        target_dir = install_dir()
        script = (
            f'powershell -NoProfile -NonInteractive -Command '
            f'"Start-Sleep -Seconds 2; Remove-Item -Recurse -Force \'{target_dir}\'"'
        )
        subprocess.Popen(
            script,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW | _DETACHED_FLAGS,
        )
    except Exception:
        _log_exception("perform_uninstall")
