import subprocess
from pathlib import Path


def update_pot(message_file="src/Resources/locales/messages.pot"):
    output_file = message_file

    exclude_dirs = {"venv", ".venv", "env", "__pycache__"}
    py_files = []

    for p in Path(".").rglob("*.py"):
        if not any(part in exclude_dirs for part in p.parts):
            py_files.append(str(p))

    if not py_files:
        print("no .py found")
        return

    cmd = [
        "xgettext",
        "--language=Python",
        "--keyword=_",
        "--keyword=gettext",
        "--keyword=N_",
        "--from-code=UTF-8",
        "--output=" + output_file,
        "--add-comments",
    ] + py_files

    print(f"{len(py_files)} Python files found. Updating {output_file}...")

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Successfully updated {output_file}")
    except FileNotFoundError:
        print(
            "❌ Error: xgettext command not found. Please ensure GNU gettext is installed."
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ xgettext execution failed: {e}")


if __name__ == "__main__":
    update_pot()
