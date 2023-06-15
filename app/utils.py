import hashlib

from pathlib import Path
from uuid import uuid4


def get_hash(data: bytes, algorithm: str = "sha256") -> str:
    return getattr(hashlib, algorithm)(data).hexdigest()


def make_tmpfile(name: str | None = None, suffix: str | None = None, touch: bool = True) -> Path:
    path = Path("/tmp").joinpath(name or str(uuid4()))
    
    if suffix:
        path = path.with_suffix(suffix)

    if touch:
        path.touch()

    return path
