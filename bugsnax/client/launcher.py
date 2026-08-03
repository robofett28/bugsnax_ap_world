"""
launcher.py - entry point registered with the Archipelago Launcher.

"""
import subprocess
import sys


def _dependency_present() -> bool:
    try:
        import pymem  # noqa: F401
        return True
    except ImportError:
        return False


def _install_dependency() -> bool:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymem"])
        return True
    except subprocess.CalledProcessError:
        return False


def _ensure_dependency() -> bool:
    if _dependency_present():
        return True

    import tkinter
    from tkinter import messagebox

    root = tkinter.Tk()
    root.withdraw()

    should_install = messagebox.askyesno(
        "Bugsnax Client - Missing Dependency",
        "The Bugsnax client needs one extra Python package Archipelago "
        "doesn't include by default: pymem.\n\n"
        "Install it now? (only required once)",
    )
    if not should_install:
        root.destroy()
        return False

    success = _install_dependency()
    if success:
        messagebox.showinfo("Bugsnax Client", "pymem installed successfully.")
    else:
        messagebox.showerror(
            "Bugsnax Client",
            "Installation failed. Try running this manually in a terminal:\n\n"
            f'"{sys.executable}" -m pip install pymem',
        )
    root.destroy()
    return success


def launch():
    import os
    import tempfile
    import traceback

    log_path = os.path.join(tempfile.gettempdir(), "bugsnax_client_error.log")

    try:
        if not _ensure_dependency():
            print("Bugsnax client cannot run without pymem. Exiting.")
            return

        from .ap_client import launch as run_client
        run_client()

    except Exception:
        tb = traceback.format_exc()
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(tb)
        except OSError:
            pass
        try:
            import tkinter
            from tkinter import messagebox
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror(
                "Bugsnax Client - Crashed on Startup",
                f"Full error log written to:\n{log_path}\n\n{tb[-1200:]}",
            )
            root.destroy()
        except Exception:
            print(tb)


if __name__ == "__main__":
    launch()
