"""Bounded PNG structural and raster validation without executing image content."""

import re
import struct
import zlib

from ..io import DataError


def validate_png(payload, relative):
    def invalid(reason):
        raise DataError(f"invalid PNG icon {relative}: {reason}")
    if payload[:8] != b"\x89PNG\r\n\x1a\n":
        invalid("signature")
    offset, chunks, image = 8, [], bytearray()
    header = None
    palette = None
    ended = False
    idat_ended = False
    while offset < len(payload):
        if len(payload) - offset < 12:
            invalid("truncated chunk header")
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        kind = payload[offset + 4:offset + 8]
        if not re.fullmatch(b"[A-Za-z]{4}", kind) or length > len(payload) - offset - 12:
            invalid("unsafe chunk type or truncated data")
        body = payload[offset + 8:offset + 8 + length]
        checksum = struct.unpack(">I", payload[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + body) != checksum:
            invalid("chunk CRC mismatch")
        offset += length + 12
        if not chunks and kind != b"IHDR":
            invalid("IHDR must be the first chunk")
        if kind == b"IHDR":
            if chunks or length != 13:
                invalid("invalid or repeated IHDR")
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            if palette is not None or b"IDAT" in chunks or not length or length % 3 or length > 768:
                invalid("invalid palette")
            palette = body
        elif kind == b"IDAT":
            if idat_ended:
                invalid("IDAT chunks must be contiguous")
            image.extend(body)
        elif kind == b"IEND":
            if length or offset != len(payload):
                invalid("IEND must be empty and final")
            ended = True
        elif kind[0] < ord("a"):
            invalid("unsupported critical chunk")
        if b"IDAT" in chunks and kind != b"IDAT":
            idat_ended = True
        chunks.append(kind)
    if not ended or header is None or not image:
        invalid("requires complete IHDR, IDAT and IEND")
    width, height, bits, color, compression, filtering, interlace = header
    if width != height or not 48 <= width <= 4096:
        invalid("must be square and 48..4096 pixels")
    bit_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if color not in bit_depths or bits not in bit_depths[color] or compression or filtering or interlace not in (0, 1):
        invalid("unsupported raster format")
    if color == 3 and (palette is None or len(palette) > 3 * (2 ** bits)):
        invalid("indexed image requires a matching palette")
    if palette is not None and color in (0, 4):
        invalid("grayscale image cannot have a palette")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    passes = [(0, 0, 1, 1)] if interlace == 0 else [(0, 0, 8, 8), (4, 0, 8, 8),
        (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
    rows = []
    for x, y, step_x, step_y in passes:
        columns = max(0, (width - x + step_x - 1) // step_x)
        count = max(0, (height - y + step_y - 1) // step_y)
        if columns and count:
            rows.extend([1 + (columns * channels * bits + 7) // 8] * count)
    expected = sum(rows)
    try:
        decoder = zlib.decompressobj()
        raster = decoder.decompress(bytes(image), expected + 1)
    except zlib.error as exc:
        invalid(f"invalid compressed image data: {exc}")
    if len(raster) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        invalid("compressed image size/stream differs from raster dimensions")
    position = 0
    for row in rows:
        if raster[position] > 4:
            invalid("invalid raster filter")
        position += row
