from app.core.config import settings


def ensure_runtime_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / "resumes").mkdir(parents=True, exist_ok=True)
