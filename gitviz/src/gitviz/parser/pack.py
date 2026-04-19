"""Pack file parser for git .git/objects/pack/."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import BinaryIO

from ..models.errors import PackFileError, ObjectNotFound
from .base import BaseParser


class PackIndex:
    """Git pack index file (.idx) reader."""

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.offset_map: dict[bytes, int] = {}
        self.crc32_map: dict[bytes, int] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load pack index file."""
        with open(self.index_path, "rb") as f:
            self._parse_index(f)

    def _parse_index(self, f: BinaryIO) -> None:
        """Parse pack index file (v2 format)."""
        header = f.read(4)
        if header != b"\xff\x74\x4f\x63":
            raise PackFileError(f"Invalid pack index signature: {header}")

        version_bytes = f.read(4)
        version = struct.unpack(">I", version_bytes)[0]
        if version != 2:
            raise PackFileError(f"Unsupported pack index version: {version}")

        fanout_bytes = f.read(256 * 4)
        fanout = struct.unpack(">256I", fanout_bytes)

        num_objects = fanout[255]

        offset_entries = 8 + 256 * 4 + num_objects * 24 + 20
        f.seek(offset_entries)
        pack_offsets = f.read(num_objects * 4)

        f.seek(8 + 256 * 4)
        sha1_entries = f.read(num_objects * 20)

        for i in range(num_objects):
            sha1 = sha1_entries[i * 20 : (i + 1) * 20]
            offset = struct.unpack(">I", pack_offsets[i * 4 : (i + 1) * 4])[0]
            self.offset_map[sha1] = offset

    def find_offset(self, oid: bytes) -> int | None:
        """Find pack file offset for object OID."""
        return self.offset_map.get(oid)


class PackFileParser(BaseParser):
    """
    Parses git pack files (.pack) with index (.idx).

    Pack file format:
    - 4-byte signature: 'PACK'
    - 4-byte version: 2 or 3
    - 4-byte object count
    - Object entries (compressed deltas/whole objects)
    - 20-byte trailing SHA-1 checksum
    """

    def __init__(self, pack_path: Path, index_path: Path):
        super().__init__(pack_path.parent.parent)
        self.pack_path = pack_path
        self.index = PackIndex(index_path)
        self.pack_offset = 0

    def get_object(self, oid: bytes) -> tuple[int, bytes]:
        """Get object from pack file by OID."""
        offset = self.index.find_offset(oid)
        if offset is None:
            raise ObjectNotFound(f"Object not found in pack: {oid.hex()}")
        return self._read_object_at(offset)

    def _read_object_at(self, offset: int) -> tuple[int, bytes]:
        """Read and decompress object at specific offset."""
        with open(self.pack_path, "rb") as f:
            f.seek(offset)
            obj_type, size, data = self._read_object_entry(f)
            return obj_type, data

    def _read_object_entry(self, f: BinaryIO) -> tuple[int, int, bytes]:
        """Read object entry from pack file."""
        c = f.read(1)[0]

        obj_type = (c >> 4) & 0x07
        size = c & 0x0F
        shift = 4

        while c & 0x80:
            c = f.read(1)[0]
            size += (c & 0x7F) << shift
            shift += 7

        compressed_size = 8192
        while True:
            chunk = f.read(min(compressed_size, 1024 * 1024))
            if not chunk:
                break
            try:
                decompressed = zlib.decompress(chunk)
                break
            except zlib.error:
                compressed_size = len(chunk) * 2
                if compressed_size > 10 * 1024 * 1024:
                    raise PackFileError("Failed to decompress pack object")

        if obj_type == 6:
            return self._resolve_ofs_delta(f, size, decompressed)
        elif obj_type == 7:
            return self._resolve_ref_delta(f, size, decompressed)

        return obj_type, size, decompressed

    def _resolve_ofs_delta(
        self, f: BinaryIO, size: int, base_data: bytes
    ) -> tuple[int, int, bytes]:
        """Resolve offset delta object."""
        f.seek(self.pack_offset)
        raise PackFileError("Offset delta resolution not yet implemented")

    def _resolve_ref_delta(
        self, f: BinaryIO, size: int, delta_data: bytes
    ) -> tuple[int, int, bytes]:
        """Resolve reference delta object."""
        base_oid = f.read(20)

        try:
            base_type, base_content = self.get_object(base_oid)
        except ObjectNotFound:
            raise PackFileError(f"Base object not found: {base_oid.hex()}")

        result = self._apply_delta(delta_data, base_content, size)
        return base_type, size, result

    def _apply_delta(self, delta: bytes, base: bytes, result_size: int) -> bytes:
        """Apply delta to base object."""
        idx = 0

        src_size, delta = self._read_varint(delta, idx)
        idx += len(delta) - len(delta.lstrip(b"\x00")) if delta else 0

        _, delta_rem = self._read_varint(delta, idx)
        idx += len(delta_rem) - len(delta_rem.lstrip(b"\x00")) if delta_rem else 0

        result = bytearray()

        while idx < len(delta):
            op = delta[idx]
            idx += 1

            if op & 0x80:
                copy_offset = 0
                copy_size = 0

                if op & 0x01:
                    copy_offset = delta[idx]
                    idx += 1
                if op & 0x02:
                    copy_offset |= delta[idx] << 8
                    idx += 1
                if op & 0x04:
                    copy_offset |= delta[idx] << 16
                    idx += 1
                if op & 0x08:
                    copy_offset |= delta[idx] << 24
                    idx += 1

                if op & 0x10:
                    copy_size = delta[idx]
                    idx += 1
                if op & 0x20:
                    copy_size |= delta[idx] << 8
                    idx += 1
                if op & 0x40:
                    copy_size |= delta[idx] << 16
                    idx += 1
                if op & 0x80:
                    copy_size |= delta[idx] << 24
                    idx += 1

                if copy_size == 0:
                    copy_size = 0x10000

                result.extend(base[copy_offset : copy_offset + copy_size])
            elif op > 0:
                result.extend(delta[idx : idx + op])
                idx += op
            else:
                break

        return bytes(result[:result_size])

    def _read_varint(self, data: bytes, offset: int) -> tuple[int, bytes]:
        """Read variable-length integer from delta."""
        value = 0
        shift = 0
        while offset < len(data):
            c = data[offset]
            offset += 1
            value |= (c & 0x7F) << shift
            if not (c & 0x80):
                break
            shift += 7
        return value, data[offset:]

    def list_objects(self) -> Iterator[tuple[bytes, int]]:
        """Iterate all objects in pack file with their offsets."""
        for oid, offset in self.index.offset_map.items():
            yield oid, offset

    def has_object(self, oid: bytes) -> bool:
        """Check if object exists in pack."""
        return oid in self.index.offset_map
