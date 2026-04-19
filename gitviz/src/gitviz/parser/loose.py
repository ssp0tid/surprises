"""Loose object reader for git .git/objects/."""

from __future__ import annotations

import zlib
from pathlib import Path
from typing import Iterator

from ..models.errors import ObjectNotFound
from .base import BaseParser


class ObjectType:
    """Git object types."""

    COMMIT = 1
    TREE = 2
    BLOB = 3
    TAG = 4
    OFS_DELTA = 6
    REF_DELTA = 7


class LooseObjectReader(BaseParser):
    """Reads uncompressed objects from .git/objects/."""

    def __init__(self, objects_dir: Path):
        super().__init__(objects_dir.parent)
        self.objects_dir = objects_dir

    def get_object(self, oid: bytes) -> tuple[int, bytes]:
        """
        Read object by SHA-1 hash.

        Returns:
            Tuple of (object_type, decompressed_content)

        Raises:
            ObjectNotFound: Object doesn't exist
        """
        hex_oid = oid.hex()
        obj_path = self.objects_dir / hex_oid[:2] / hex_oid[2:]

        if not obj_path.exists():
            raise ObjectNotFound(f"Object not found: {hex_oid}")

        with open(obj_path, "rb") as f:
            compressed = f.read()

        return self._decompress_object(compressed)

    def _decompress_object(self, compressed: bytes) -> tuple[int, bytes]:
        """Decompress git object and return type and content."""
        decompressed = zlib.decompress(compressed)

        type_map = {
            b"commit": ObjectType.COMMIT,
            b"tree": ObjectType.TREE,
            b"blob": ObjectType.BLOB,
            b"tag": ObjectType.TAG,
        }

        space_idx = decompressed.index(b" ")
        obj_type_str = decompressed[:space_idx]
        obj_type = type_map.get(obj_type_str, 0)

        null_idx = decompressed.index(b"\x00")
        content = decompressed[null_idx + 1 :]

        return obj_type, content

    def list_objects(self) -> Iterator[bytes]:
        """Iterate all loose object OIDs."""
        for dir_name in self.objects_dir.iterdir():
            if not dir_name.is_dir() or len(dir_name.name) != 2:
                continue
            try:
                int(dir_name.name, 16)
            except ValueError:
                continue

            for obj_file in dir_name.iterdir():
                if obj_file.is_file() and len(obj_file.name) == 38:
                    try:
                        int(obj_file.name, 16)
                        oid_hex = dir_name.name + obj_file.name
                        yield bytes.fromhex(oid_hex)
                    except ValueError:
                        continue

    def has_object(self, oid: bytes) -> bool:
        """Check if object exists."""
        hex_oid = oid.hex()
        obj_path = self.objects_dir / hex_oid[:2] / hex_oid[2:]
        return obj_path.exists()
