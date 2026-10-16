"""Reversible character-level delta encoding for UTF-8 text snapshots."""
from difflib import SequenceMatcher
import json


def make_delta(old: str, new: str) -> bytes:
    """Encode changes from old to new as a compact JSON operation stream.

    Operations are [tag, old_length, inserted_text]. Equal operations store only
    the length; insert/replace operations store replacement text. The result is
    deterministic JSON bytes and can be compressed by the caller.
    """
    matcher = SequenceMatcher(a=old, b=new, autojunk=False)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            ops.append(["e", i2 - i1, ""])
        elif tag == "insert":
            ops.append(["i", 0, new[j1:j2]])
        elif tag == "delete":
            ops.append(["d", i2 - i1, ""])
        elif tag == "replace":
            ops.append(["r", i2 - i1, new[j1:j2]])
    return json.dumps(ops, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def apply_delta(old: str, delta: bytes) -> str:
    """Apply a delta to old text and return the exact reconstructed text."""
    ops = json.loads(delta.decode("utf-8"))
    out, pos = [], 0
    for item in ops:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError("Invalid delta operation")
        tag, length, value = item
        if not isinstance(length, int) or length < 0 or not isinstance(value, str):
            raise ValueError("Invalid delta operation values")
        if tag == "e":
            if pos + length > len(old):
                raise ValueError("Delta references beyond the previous version")
            out.append(old[pos:pos + length]); pos += length
        elif tag == "i":
            out.append(value)
        elif tag == "d":
            if pos + length > len(old):
                raise ValueError("Delta deletes beyond the previous version")
            pos += length
        elif tag == "r":
            if pos + length > len(old):
                raise ValueError("Delta replaces beyond the previous version")
            pos += length; out.append(value)
        else:
            raise ValueError(f"Unknown delta operation: {tag}")
    if pos != len(old):
        raise ValueError("Delta did not consume the full previous version")
    return "".join(out)
