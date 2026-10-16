"""Compression helpers used by Time Capsule."""
import zlib

LEVEL = 9

def compress(data: bytes) -> bytes:
    return zlib.compress(data, level=LEVEL)

def decompress(data: bytes) -> bytes:
    return zlib.decompress(data)
