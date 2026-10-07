import fcntl
import json
import os
import shutil
from contextlib import contextmanager, suppress
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4

from django.conf import settings

STORAGE_PREFIX = "income-attachments"
CLAIM_DIRECTORY = ".incoming"


def _fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise OSError("Private attachment directory is not a real directory.")
    os.chmod(path, 0o700)


def _incoming_root():
    return Path(settings.MEDIA_ROOT) / CLAIM_DIRECTORY


def _locks_root():
    return _incoming_root() / "locks"


def claim_path(batch_id):
    return _incoming_root() / str(UUID(str(batch_id)))


def acquire_batch_lock(batch_id, *, blocking=True):
    locks = _locks_root()
    _ensure_directory(locks.parent)
    _ensure_directory(locks)
    lock_path = locks / f"{UUID(str(batch_id))}.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    os.fchmod(descriptor, 0o600)
    _fsync_directory(locks)
    operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        fcntl.flock(descriptor, operation)
    except BlockingIOError:
        os.close(descriptor)
        return None
    return descriptor


def release_batch_lock(descriptor):
    if descriptor is None:
        return
    try:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


@contextmanager
def locked_batch(batch_id, *, blocking=True):
    descriptor = acquire_batch_lock(batch_id, blocking=blocking)
    try:
        yield descriptor
    finally:
        release_batch_lock(descriptor)


def create_claim(batch_id):
    batch_id = UUID(str(batch_id))
    root = _incoming_root()
    _ensure_directory(root)
    descriptor = acquire_batch_lock(batch_id)
    directory = claim_path(batch_id)
    created = False
    try:
        directory.mkdir(mode=0o700)
        created = True
        _fsync_directory(root)
        write_manifest(batch_id, {"batch_id": str(batch_id), "state": "receiving", "files": []})
    except Exception:
        if created:
            with suppress(OSError):
                cleanup_claim(batch_id)
        release_batch_lock(descriptor)
        raise
    return directory, descriptor


def write_manifest(batch_id, payload):
    directory = claim_path(batch_id)
    temporary = directory / f"manifest.{uuid4()}.tmp"
    target = directory / "manifest.json"
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    os.replace(temporary, target)
    _fsync_directory(directory)


def storage_key(household_id, batch_id, attachment_id):
    return str(
        PurePosixPath(
            STORAGE_PREFIX,
            str(UUID(str(household_id))),
            str(UUID(str(batch_id))),
            str(UUID(str(attachment_id))),
        )
    )


def storage_path(key):
    parts = PurePosixPath(key).parts
    if len(parts) != 4 or parts[0] != STORAGE_PREFIX:
        raise ValueError("Invalid private attachment key.")
    for value in parts[1:]:
        if str(UUID(value)) != value:
            raise ValueError("Invalid private attachment key.")
    root = Path(settings.MEDIA_ROOT)
    path = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise OSError("Attachment storage path cannot contain symbolic links.")
    return path


def promote_file(source, key):
    target = storage_path(key)
    parent = target.parent
    missing = []
    current = parent
    while current != Path(settings.MEDIA_ROOT):
        if not current.exists():
            missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)
        _fsync_directory(directory.parent)
    if target.exists():
        raise FileExistsError("Attachment storage key already exists.")
    os.replace(source, target)
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    current = target.parent
    while True:
        _fsync_directory(current)
        if current == Path(settings.MEDIA_ROOT):
            break
        current = current.parent
    return target


def unlink_key(key):
    path = storage_path(key)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    _fsync_directory(path.parent)
    return True


def cleanup_claim(batch_id):
    directory = claim_path(batch_id)
    if directory.exists():
        shutil.rmtree(directory)
        _fsync_directory(directory.parent)


def open_key(key):
    path = storage_path(key)
    return path.open("rb")
