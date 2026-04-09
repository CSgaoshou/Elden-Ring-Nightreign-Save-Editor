import zipfile
import logging
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def create_backup(save_file: str | Path, backup_dir: str | Path, max_backups=5):
    save_file = Path(save_file)
    if not save_file.exists():
        yield
        return

    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created backup directory: {backup_dir}")

    root_zip = backup_dir / "root.zip"
    if not root_zip.exists():
        output_zip = root_zip
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_zip = backup_dir / f"backup_{timestamp}.zip"

    temp_zip = output_zip.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(save_file, save_file.name)

    try:
        yield
    except Exception:
        if temp_zip.exists():
            temp_zip.unlink()
        raise
    else:
        temp_zip.rename(output_zip)
        logger.info(f"Created new backup: {output_zip}")
        if output_zip != root_zip:
            _rotate_backups(backup_dir, max_backups)


def _rotate_backups(backup_dir: Path, max_backups: int) -> None:
    backups = [p for p in backup_dir.glob("*.zip") if p.name != "root.zip"]
    if len(backups) <= max_backups:
        return

    backups.sort(key=lambda p: p.stat().st_mtime)
    excess_backups = backups[:-max_backups]

    for old_backup in excess_backups:
        old_backup.unlink(missing_ok=True)
        logger.info(f"Removed old backup: {old_backup.name}")
