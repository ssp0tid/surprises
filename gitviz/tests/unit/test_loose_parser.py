"""Tests for loose object parser."""

import pytest
import zlib
from pathlib import Path
import tempfile

from gitviz.parser.loose import LooseObjectReader, ObjectType


def test_object_type_constants():
    """Test object type constants."""
    assert ObjectType.COMMIT == 1
    assert ObjectType.TREE == 2
    assert ObjectType.BLOB == 3
    assert ObjectType.TAG == 4
    assert ObjectType.OFS_DELTA == 6
    assert ObjectType.REF_DELTA == 7


def test_decompress_object():
    """Test object decompression."""
    with tempfile.TemporaryDirectory() as tmpdir:
        objects_dir = Path(tmpdir) / "objects"
        objects_dir.mkdir()

        obj_content = b"tree " + b"4b825dc642cb6eb9a060e54bf8d69288fbee4904\x00Test tree"
        compressed = zlib.compress(obj_content)

        obj_dir = objects_dir / "ab"
        obj_dir.mkdir()
        obj_path = obj_dir / ("c" * 38)
        obj_path.write_bytes(compressed)

        reader = LooseObjectReader(objects_dir)

        oid = b"a" * 20
        obj_type, content = reader._decompress_object(compressed)
        assert obj_type == ObjectType.TREE
        assert b"Test tree" in content


def test_hex_to_bytes():
    """Test hex to bytes conversion."""
    from gitviz.parser.base import BaseParser

    result = BaseParser._hex_to_bytes("616263")
    assert result == b"abc"


def test_bytes_to_hex():
    """Test bytes to hex conversion."""
    from gitviz.parser.base import BaseParser

    result = BaseParser._bytes_to_hex(b"abc")
    assert result == "616263"
