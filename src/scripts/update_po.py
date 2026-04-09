import subprocess
from pathlib import Path

POT_FILE = "src/Resources/locales/messages.pot"
LOCALE_DIR = "src/Resources/locales"
LANGUAGES = ["en_US", "zh_CN", "zh_TW"]


def generate_or_update_po_gnu():
    if not Path(POT_FILE).exists():
        print(f"❌ Not found {POT_FILE}")
        return

    for lang in LANGUAGES:
        lc_messages_dir = Path(LOCALE_DIR) / lang / "LC_MESSAGES"
        lc_messages_dir.mkdir(parents=True, exist_ok=True)

        po_file = lc_messages_dir / f"{lang}.po"

        if not po_file.exists():
            print(f"[{lang}] init...")
            cmd = [
                "msginit",
                "--no-translator",
                f"--input={POT_FILE}",
                f"--output-file={po_file}",
                f"--locale={lang}",
            ]
        else:
            print(f"[{lang}] update...")
            cmd = [
                "msgmerge",
                "-U",
                "--backup=none",
                str(po_file),
                POT_FILE,
            ]

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print(f"✅ [{lang}] Successfully updated -> {po_file}")
        except FileNotFoundError:
            print(
                "❌ Error: gettext tools not found. Please ensure GNU gettext is installed."
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ [{lang}] Execution failed: {e}")


if __name__ == "__main__":
    generate_or_update_po_gnu()
