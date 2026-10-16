"""Persistence and reconstruction for local Time Capsule projects."""
from __future__ import annotations
import base64, json, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from .compression import compress, decompress
from .delta_engine import make_delta, apply_delta
from .integrity import sha256_text

FORMAT_VERSION = 1

class CapsuleError(Exception):
    pass

def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")

def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)

def new_capsule(name: str, filename: str) -> dict:
    return {"format_version": FORMAT_VERSION, "id": uuid.uuid4().hex, "name": name.strip(),
            "filename": filename, "created_at": _now(), "versions": []}

def add_version(capsule: dict, text: str, label: str = "") -> dict:
    if not isinstance(text, str):
        raise TypeError("Time Capsule currently supports UTF-8 text files only.")
    versions = capsule.setdefault("versions", [])
    if versions:
        previous = reconstruct_version(capsule, len(versions) - 1)
        delta = make_delta(previous, text)
        payload = compress(delta)
        kind = "delta"
        full_copy_bytes = len(compress(text.encode("utf-8")))
    else:
        payload = compress(text.encode("utf-8"))
        kind = "baseline"
        full_copy_bytes = len(payload)
    entry = {"id": uuid.uuid4().hex[:10], "number": len(versions) + 1,
             "label": label.strip() or f"Version {len(versions) + 1}", "created_at": _now(),
             "kind": kind, "payload_b64": _b64(payload), "payload_bytes": len(payload),
             "raw_bytes": len(text.encode("utf-8")), "sha256": sha256_text(text),
             "full_copy_compressed_bytes": full_copy_bytes}
    versions.append(entry)
    return entry

def reconstruct_version(capsule: dict, index: int) -> str:
    versions = capsule.get("versions", [])
    if index < 0 or index >= len(versions):
        raise IndexError("Version does not exist")
    current = ""
    for i in range(index + 1):
        entry = versions[i]
        try:
            payload = decompress(_unb64(entry["payload_b64"]))
            if entry["kind"] == "baseline":
                current = payload.decode("utf-8")
            elif entry["kind"] == "delta":
                current = apply_delta(current, payload)
            else:
                raise CapsuleError("Unknown stored version type")
        except Exception as exc:
            raise CapsuleError(f"Could not reconstruct version {i + 1}: {exc}") from exc
        if sha256_text(current) != entry.get("sha256"):
            raise CapsuleError(f"Integrity check failed for version {i + 1}")
    return current

def storage_stats(capsule: dict) -> dict:
    versions = capsule.get("versions", [])
    actual = sum(int(v.get("payload_bytes", 0)) for v in versions)
    full = sum(int(v.get("full_copy_compressed_bytes", 0)) for v in versions)
    raw = sum(int(v.get("raw_bytes", 0)) for v in versions)
    saved = (1 - actual / full) * 100 if full else 0.0
    return {"actual_bytes": actual, "full_copy_bytes": full, "raw_bytes": raw,
            "saved_percent": saved, "version_count": len(versions)}

def save_capsule(capsule: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{capsule['id']}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(capsule, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
    return path

def load_capsule(path: Path) -> dict:
    capsule = json.loads(path.read_text(encoding="utf-8"))
    validate_capsule(capsule)
    return capsule

def validate_capsule(capsule: dict) -> None:
    if not isinstance(capsule, dict) or capsule.get("format_version") != FORMAT_VERSION:
        raise CapsuleError("Unsupported or invalid Time Capsule archive.")
    if not isinstance(capsule.get("versions"), list) or not capsule.get("id"):
        raise CapsuleError("Archive is missing required fields.")
    for i, v in enumerate(capsule["versions"]):
        for key in ("kind", "payload_b64", "sha256", "raw_bytes", "payload_bytes"):
            if key not in v:
                raise CapsuleError(f"Version {i + 1} is missing {key}.")
        if v["kind"] not in ("baseline", "delta"):
            raise CapsuleError(f"Version {i + 1} has an invalid storage type.")
        _unb64(v["payload_b64"])
    if capsule.get("versions") and capsule["versions"][0]["kind"] != "baseline":
        raise CapsuleError("First version must be a baseline.")

def capsule_archive_bytes(capsule: dict) -> bytes:
    return json.dumps(capsule, ensure_ascii=False, indent=2).encode("utf-8")
