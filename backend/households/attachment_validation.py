import struct
import unicodedata
import zlib
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_DIMENSION = 12_000
MAX_IMAGE_PIXELS = 40_000_000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class AttachmentValidationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def normalize_filename(value):
    normalized = unicodedata.normalize("NFKC", str(value)).replace("\\", "/")
    normalized = normalized.rsplit("/", 1)[-1]
    normalized = "".join(
        character for character in normalized if unicodedata.category(character) not in {"Cc", "Cf"}
    ).strip()
    if not normalized or normalized in {".", ".."}:
        raise AttachmentValidationError("invalid_filename", "Podaj poprawną nazwę pliku.")
    if len(normalized) > 255:
        raise AttachmentValidationError("invalid_filename", "Nazwa pliku może mieć do 255 znaków.")
    return normalized


def _image_dimensions(width, height):
    if (
        width < 1
        or height < 1
        or width > MAX_IMAGE_DIMENSION
        or height > MAX_IMAGE_DIMENSION
        or width * height > MAX_IMAGE_PIXELS
    ):
        raise AttachmentValidationError("invalid_dimensions", "Wymiary obrazu przekraczają limit.")


def _validate_png(path):
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        if stream.read(8) != PNG_SIGNATURE:
            raise AttachmentValidationError(
                "unsupported_file_type", "Obsługiwane są pliki PNG, JPG i PDF."
            )
        offset = 8
        seen_ihdr = False
        seen_idat = False
        seen_iend = False
        while offset < file_size:
            header = stream.read(8)
            if len(header) != 8:
                raise AttachmentValidationError("invalid_file", "Plik PNG jest uszkodzony.")
            length, chunk_type = struct.unpack(">I4s", header)
            offset += 8
            if not all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in chunk_type):
                raise AttachmentValidationError("invalid_file", "Plik PNG jest uszkodzony.")
            if length > file_size - offset - 4:
                raise AttachmentValidationError("invalid_file", "Plik PNG jest ucięty.")
            if not seen_ihdr and chunk_type != b"IHDR":
                raise AttachmentValidationError(
                    "invalid_file", "Plik PNG nie zawiera nagłówka IHDR."
                )
            if chunk_type == b"IHDR":
                if seen_ihdr or length != 13:
                    raise AttachmentValidationError(
                        "invalid_file", "Nagłówek PNG jest niepoprawny."
                    )
                dimensions = stream.read(8)
                width, height = struct.unpack(">II", dimensions)
                _image_dimensions(width, height)
                crc = zlib.crc32(chunk_type)
                crc = zlib.crc32(dimensions, crc)
                remaining = length - len(dimensions)
                while remaining:
                    chunk = stream.read(min(64 * 1024, remaining))
                    if not chunk:
                        raise AttachmentValidationError("invalid_file", "Plik PNG jest ucięty.")
                    crc = zlib.crc32(chunk, crc)
                    remaining -= len(chunk)
                seen_ihdr = True
            else:
                if chunk_type == b"IDAT":
                    seen_idat = True
                if chunk_type == b"IEND":
                    if length != 0 or not seen_idat:
                        raise AttachmentValidationError(
                            "invalid_file", "Plik PNG jest niekompletny."
                        )
                    seen_iend = True
                crc = zlib.crc32(chunk_type)
                remaining = length
                while remaining:
                    chunk = stream.read(min(64 * 1024, remaining))
                    if not chunk:
                        raise AttachmentValidationError("invalid_file", "Plik PNG jest ucięty.")
                    crc = zlib.crc32(chunk, crc)
                    remaining -= len(chunk)
            expected_crc = stream.read(4)
            if len(expected_crc) != 4 or struct.unpack(">I", expected_crc)[0] != crc & 0xFFFFFFFF:
                raise AttachmentValidationError(
                    "invalid_file", "Suma kontrolna PNG jest niepoprawna."
                )
            offset += length + 4
            if seen_iend:
                if offset != file_size:
                    raise AttachmentValidationError(
                        "invalid_file", "Plik PNG ma dane po końcu dokumentu."
                    )
                return "image/png"
        raise AttachmentValidationError("invalid_file", "Plik PNG nie ma końcowego znacznika IEND.")


def _read_marker(stream):
    if stream.read(1) != b"\xff":
        raise AttachmentValidationError("invalid_file", "Struktura JPEG jest niepoprawna.")
    marker = stream.read(1)
    while marker == b"\xff":
        marker = stream.read(1)
    if not marker or marker == b"\x00":
        raise AttachmentValidationError("invalid_file", "Struktura JPEG jest niepoprawna.")
    return marker[0]


def _validate_jpeg(path):
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        if stream.read(2) != b"\xff\xd8":
            raise AttachmentValidationError(
                "unsupported_file_type", "Obsługiwane są pliki PNG, JPG i PDF."
            )
        has_frame = False
        has_scan = False
        frame_components = set()
        pending_marker = None
        while True:
            marker = pending_marker if pending_marker is not None else _read_marker(stream)
            pending_marker = None
            if marker == 0xD9:
                if not has_frame or not has_scan or stream.read(1):
                    raise AttachmentValidationError("invalid_file", "Plik JPEG jest niekompletny.")
                return "image/jpeg"
            if marker in {0xD8, 0x01, *range(0xD0, 0xD8)}:
                continue
            raw_length = stream.read(2)
            if len(raw_length) != 2:
                raise AttachmentValidationError("invalid_file", "Segment JPEG jest ucięty.")
            length = struct.unpack(">H", raw_length)[0]
            if length < 2 or length - 2 > file_size - stream.tell():
                raise AttachmentValidationError(
                    "invalid_file", "Długość segmentu JPEG jest niepoprawna."
                )
            segment = stream.read(length - 2)
            if len(segment) != length - 2:
                raise AttachmentValidationError("invalid_file", "Segment JPEG jest ucięty.")
            if marker in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                if has_frame or len(segment) < 6:
                    raise AttachmentValidationError(
                        "invalid_file", "Nagłówek JPEG jest niepoprawny."
                    )
                precision, height, width, component_count = struct.unpack(">BHHB", segment[:6])
                if (
                    precision not in {8, 12}
                    or component_count < 1
                    or len(segment) != 6 + component_count * 3
                ):
                    raise AttachmentValidationError(
                        "invalid_file", "Liczba komponentów JPEG jest niepoprawna."
                    )
                for offset in range(6, len(segment), 3):
                    component_id, sampling, quantization_table = segment[offset : offset + 3]
                    if (
                        component_id in frame_components
                        or sampling >> 4 not in range(1, 5)
                        or sampling & 0x0F not in range(1, 5)
                        or quantization_table > 3
                    ):
                        raise AttachmentValidationError(
                            "invalid_file", "Parametry komponentu JPEG są niepoprawne."
                        )
                    frame_components.add(component_id)
                _image_dimensions(width, height)
                has_frame = True
            if marker == 0xDA:
                if not has_frame or len(segment) < 6:
                    raise AttachmentValidationError(
                        "invalid_file", "Nagłówek SOS JPEG jest niepoprawny."
                    )
                scan_component_count = segment[0]
                if scan_component_count < 1 or len(segment) != 4 + 2 * scan_component_count:
                    raise AttachmentValidationError(
                        "invalid_file", "Lista komponentów SOS jest niepoprawna."
                    )
                scan_components = set()
                for offset in range(1, 1 + 2 * scan_component_count, 2):
                    component_id = segment[offset]
                    tables = segment[offset + 1]
                    if (
                        component_id not in frame_components
                        or component_id in scan_components
                        or tables >> 4 > 3
                        or tables & 0x0F > 3
                    ):
                        raise AttachmentValidationError(
                            "invalid_file", "Komponent SOS JPEG jest niepoprawny."
                        )
                    scan_components.add(component_id)
                spectral_start, spectral_end, successive_approximation = segment[-3:]
                if (
                    spectral_start > spectral_end
                    or spectral_end > 63
                    or successive_approximation >> 4 > 13
                    or successive_approximation & 0x0F > 13
                ):
                    raise AttachmentValidationError(
                        "invalid_file", "Parametry skanu JPEG są niepoprawne."
                    )
                has_scan = True
            if marker == 0xDA:
                while True:
                    value = stream.read(1)
                    if not value:
                        raise AttachmentValidationError(
                            "invalid_file", "Plik JPEG nie ma znacznika EOI."
                        )
                    if value != b"\xff":
                        continue
                    next_value = stream.read(1)
                    while next_value == b"\xff":
                        next_value = stream.read(1)
                    if not next_value:
                        raise AttachmentValidationError("invalid_file", "Plik JPEG jest ucięty.")
                    code = next_value[0]
                    if code == 0x00 or 0xD0 <= code <= 0xD7:
                        continue
                    if code == 0xD9:
                        if not has_frame or stream.read(1):
                            raise AttachmentValidationError(
                                "invalid_file", "Plik JPEG jest niekompletny."
                            )
                        return "image/jpeg"
                    pending_marker = code
                    break


def _validate_pdf(path):
    with path.open("rb") as stream:
        header = stream.read(8)
        version = header[5:8]
        valid_version = (
            len(header) == 8
            and header[:5] == b"%PDF-"
            and version[0:1] in {b"1", b"2"}
            and version[1:2] == b"."
            and version[2:3].isdigit()
            and (version[0:1] != b"1" or version[2:3] <= b"7")
            and (version[0:1] != b"2" or version[2:3] == b"0")
        )
        if not valid_version:
            raise AttachmentValidationError(
                "unsupported_file_type", "Obsługiwane są pliki PNG, JPG i PDF."
            )
        size = path.stat().st_size
        stream.seek(max(0, size - 1024))
        ending = stream.read()
        marker = ending.rfind(b"%%EOF")
        if marker < 0 or ending[marker + 5 :].strip(b"\t\n\r\f "):
            raise AttachmentValidationError(
                "invalid_file", "Dokument PDF nie ma poprawnego znacznika końca."
            )
    return "application/pdf"


def validate_attachment(path, original_name):
    path = Path(path)
    size = path.stat().st_size
    if size < 1 or size > MAX_FILE_BYTES:
        raise AttachmentValidationError(
            "attachment_upload_limit_exceeded", "Plik przekracza limit 10 MiB."
        )
    with path.open("rb") as stream:
        signature = stream.read(8)
    extension = Path(original_name).suffix.lower()
    if signature.startswith(PNG_SIGNATURE):
        media_type = _validate_png(path)
        extensions = {".png"}
    elif signature.startswith(b"\xff\xd8"):
        media_type = _validate_jpeg(path)
        extensions = {".jpg", ".jpeg"}
    elif signature.startswith(b"%PDF-"):
        media_type = _validate_pdf(path)
        extensions = {".pdf"}
    else:
        raise AttachmentValidationError(
            "unsupported_file_type", "Obsługiwane są pliki PNG, JPG i PDF."
        )
    if extension not in extensions:
        raise AttachmentValidationError(
            "file_extension_mismatch", "Rozszerzenie nie pasuje do zawartości pliku."
        )
    return media_type, size
