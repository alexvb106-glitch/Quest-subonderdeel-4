"""Minimale PDF-schrijver voor de tests van de ingang (slice S1.2).

Maakt kleine PDF-bestanden met een exact instelbare inhoud per pagina: tekst
(zichtbaar of als onzichtbare OCR-laag), lijnen, rechthoeken, curves en afbeeldingen.
Geen extra dependency: alleen de standaardbibliotheek (zlib, hashlib, struct).
Dit is een hulpmodule voor de tests, geen testbestand zelf, en geen productiecode.
"""

import hashlib
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

# Paginaformaten in PDF-punten (staand)
A4 = (595.0, 842.0)
A0 = (2384.0, 3370.0)


# Eén afbeelding op een pagina. De pixelresolutie (eigen grootte van het beeld)
# staat los van de plaatsing op het blad. Zonder draw_width/draw_height wordt de
# afbeelding paginavullend geplaatst.
@dataclass
class ImageSpec:
    width_px: int
    height_px: int
    x: float = 0.0
    y: float = 0.0
    draw_width: float | None = None
    draw_height: float | None = None


# Inhoud van één pagina. invisible_text=True schrijft de tekst met tekstweergavemodus 3
# (onzichtbaar), zoals een OCR-laag boven een scan.
@dataclass
class PageSpec:
    size: tuple[float, float] = A4
    text: str | None = None
    invisible_text: bool = False
    lines: int = 0
    rects: int = 0
    curves: int = 0
    images: list[ImageSpec] = field(default_factory=list)


# Opvulreeks en vaste waarden voor de standaardbeveiliging (revisie 2, RC4 40 bit)
_PASSWORD_PADDING = bytes.fromhex(
    "28BF4E5E4E758A4164004E56FFFA01082E2E00B6D0683E802F0CA9FE6453697A"
)
_PERMISSIONS = -44
_DOCUMENT_ID = hashlib.md5(b"onderdeel4-testbestand").digest()


# RC4-versleuteling (symmetrisch: dezelfde functie ontsleutelt ook)
def _rc4(key: bytes, data: bytes) -> bytes:
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) % 256
        state[i], state[j] = state[j], state[i]
    result = bytearray()
    i = j = 0
    for byte in data:
        i = (i + 1) % 256
        j = (j + state[i]) % 256
        state[i], state[j] = state[j], state[i]
        result.append(byte ^ state[(state[i] + state[j]) % 256])
    return bytes(result)


# Wachtwoord aanvullen of afkappen tot 32 bytes met de vaste opvulreeks
def _pad_password(password: str) -> bytes:
    return (password.encode("latin-1") + _PASSWORD_PADDING)[:32]


# Sleutels en O/U-waarden volgens de PDF-standaard (Algorithm 3.2 t/m 3.4, revisie 2)
def _encryption_values(user_password: str, owner_password: str) -> tuple[bytes, bytes, bytes]:
    owner_key = hashlib.md5(_pad_password(owner_password)).digest()[:5]
    owner_value = _rc4(owner_key, _pad_password(user_password))
    file_key = hashlib.md5(
        _pad_password(user_password)
        + owner_value
        + struct.pack("<i", _PERMISSIONS)
        + _DOCUMENT_ID
    ).digest()[:5]
    user_value = _rc4(file_key, _PASSWORD_PADDING)
    return file_key, owner_value, user_value


# Sleutel per object (Algorithm 3.1): bestandssleutel plus objectnummer en generatie 0
def _object_key(file_key: bytes, object_number: int) -> bytes:
    material = file_key + struct.pack("<i", object_number)[:3] + b"\x00\x00"
    return hashlib.md5(material).digest()[: len(file_key) + 5]


# Tekst veilig in een PDF-string zetten (alleen ASCII nodig in de tests)
def _escape_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


# Contentstream van één pagina: eerst afbeeldingen, daarna lijnen, rechthoeken, curves en tekst
def _content_stream(page: PageSpec) -> bytes:
    width, height = page.size
    ops: list[str] = []

    for index, image in enumerate(page.images):
        draw_width = image.draw_width if image.draw_width is not None else width
        draw_height = image.draw_height if image.draw_height is not None else height
        ops.append(
            f"q {draw_width} 0 0 {draw_height} {image.x} {image.y} cm /Im{index} Do Q"
        )

    # Lijnen: elk een eigen pad (m ... l S), verdeeld over de hoogte van het blad
    for index in range(page.lines):
        y = 20 + index * (height - 40) / max(page.lines, 1)
        ops.append(f"20 {y:.2f} m {width - 20} {y:.2f} l S")

    # Rechthoeken: elk een eigen re-operator, kleine vakjes langs de linkerrand
    for index in range(page.rects):
        y = 20 + index * (height - 40) / max(page.rects, 1)
        ops.append(f"30 {y:.2f} 10 5 re S")

    # Curves: elk een eigen pad met één Bézier-segment (m ... c S), langs de rechterrand
    for index in range(page.curves):
        y = 20 + index * (height - 40) / max(page.curves, 1)
        ops.append(
            f"{width - 60} {y:.2f} m {width - 55} {y + 5:.2f} "
            f"{width - 45} {y + 5:.2f} {width - 40} {y:.2f} c S"
        )

    if page.text:
        render_mode = 3 if page.invisible_text else 0
        ops.append(
            f"BT /F1 12 Tf {render_mode} Tr 50 {height / 2:.2f} Td "
            f"({_escape_text(page.text)}) Tj ET"
        )

    return "\n".join(ops).encode("latin-1")


# Grijswaardenafbeelding (8 bit) met FlateDecode, zodat ook een groot beeld een klein bestand geeft
def _image_stream(image: ImageSpec) -> tuple[bytes, bytes]:
    pixels = zlib.compress(bytes(image.width_px * image.height_px))
    header = (
        f"/Type /XObject /Subtype /Image /Width {image.width_px} /Height {image.height_px} "
        f"/ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode"
    ).encode("latin-1")
    return header, pixels


def write_pdf(path: Path, pages: list[PageSpec], user_password: str | None = None) -> Path:
    """Schrijf een PDF met de opgegeven pagina's naar path en geef path terug.

    Met user_password wordt het bestand versleuteld (RC4 40 bit, revisie 2), zodat
    het zonder dat wachtwoord niet te openen is. Een lege lijst pages geeft een
    geldige PDF met 0 pagina's.
    """
    # Objecten verzamelen als (kop, stream of None); objectnummer = index + 1
    objects: list[tuple[bytes, bytes | None]] = []

    def add(header: bytes, stream: bytes | None = None) -> int:
        objects.append((header, stream))
        return len(objects)

    catalog_number = add(b"")  # wordt hieronder ingevuld zodra het Pages-nummer bekend is
    pages_number = add(b"")
    font_number = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Per pagina: afbeeldingen, contentstream en het pagina-object zelf
    page_numbers: list[int] = []
    for page in pages:
        image_refs = []
        for index, image in enumerate(page.images):
            header, data = _image_stream(image)
            image_refs.append(f"/Im{index} {add(header, data)} 0 R")
        content_number = add(b"", _content_stream(page))
        xobjects = f"/XObject << {' '.join(image_refs)} >>" if image_refs else ""
        width, height = page.size
        page_numbers.append(
            add(
                (
                    f"<< /Type /Page /Parent {pages_number} 0 R "
                    f"/MediaBox [0 0 {width} {height}] "
                    f"/Resources << /Font << /F1 {font_number} 0 R >> {xobjects} >> "
                    f"/Contents {content_number} 0 R >>"
                ).encode("latin-1")
            )
        )

    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[catalog_number - 1] = (f"<< /Type /Catalog /Pages {pages_number} 0 R >>".encode(), None)
    objects[pages_number - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode(),
        None,
    )

    # Optionele versleuteling: streams per object versleutelen, Encrypt-object achteraan
    file_key = None
    encrypt_number = None
    if user_password is not None:
        file_key, owner_value, user_value = _encryption_values(user_password, "eigenaar")
        encrypt_number = add(
            (
                f"<< /Filter /Standard /V 1 /R 2 /O <{owner_value.hex()}> "
                f"/U <{user_value.hex()}> /P {_PERMISSIONS} >>"
            ).encode("latin-1")
        )

    # Bestand opbouwen met kop, objecten, xref-tabel en trailer
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, (header, stream) in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode()
        if stream is None:
            output += header
        else:
            if file_key is not None and number != encrypt_number:
                stream = _rc4(_object_key(file_key, number), stream)
            # Een lege kop betekent: alleen /Length (contentstream)
            inner = header[2:-2] if header.startswith(b"<<") else header
            output += b"<< " + inner + f" /Length {len(stream)} >>\nstream\n".encode()
            output += stream + b"\nendstream"
        output += b"\nendobj\n"

    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()

    encrypt_entry = f" /Encrypt {encrypt_number} 0 R" if encrypt_number else ""
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_number} 0 R{encrypt_entry} "
        f"/ID [<{_DOCUMENT_ID.hex()}> <{_DOCUMENT_ID.hex()}>] >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    path.write_bytes(bytes(output))
    return path


def write_raw_pdf(path: Path, objects: list[bytes], root: int = 1) -> Path:
    """Schrijf een PDF met letterlijk opgegeven objectinhoud (objectnummer = index + 1).

    Voor kwaadwillige of kapotte structuren die write_pdf bewust niet kan maken,
    zoals een object dat naar zichzelf verwijst. De xref-tabel klopt wel.
    """
    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {root} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(output))
    return path
