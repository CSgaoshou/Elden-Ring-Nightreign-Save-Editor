import subprocess
from pathlib import Path


def compile_po_to_mo(locales_dir: Path):
    print(f"Locales dir: {locales_dir.absolute()}")
    # Find all .po files recursively (rglob)
    po_files = list(locales_dir.rglob("*.po"))

    print(f"Found {len(po_files)} files to compile.")

    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        print(f"Compiling: {po_path} -> {mo_path}")
        # check=True ensures the script stops if there is a syntax error in a .po file
        subprocess.run(["msgfmt", str(po_path), "-o", str(mo_path)], check=True)

    print("All files compiled successfully.")


if __name__ == "__main__":
    compile_po_to_mo(Path("src/Resources/locales"))
