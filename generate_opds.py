#!/usr/bin/env python3
import os, urllib.parse, xml.etree.ElementTree as ET, datetime, re

FEED_NS = "http://www.w3.org/2005/Atom"
OPDS_NS = "http://opds-spec.org/2010/catalog"
ET.register_namespace("", FEED_NS)
ET.register_namespace("opds", OPDS_NS)

BOOKS_DIR = "books"
ALLOWED_EXT = (".epub", ".mobi", ".azw3", ".pdf", ".cbz", ".cbr")
MIME_MAP = {
    ".epub": "application/epub+zip",
    ".mobi": "application/x-mobipocket-ebook",
    ".azw3": "application/vnd.amazon.ebook",
    ".pdf": "application/pdf",
    ".cbz": "application/zip",
    ".cbr": "application/x-rar-compressed"
}


def sanitize(text):
    """Elimina caracteres no válidos para nombres de archivo."""
    text = text.strip()
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text[:100]  # límite razonable de longitud


def get_metadata_epub(filepath):
    try:
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(filepath, options={"ignore_ncx": True})
        title = book.get_metadata('DC', 'title')
        author = book.get_metadata('DC', 'creator')
        title = title[0][0] if title else None
        author = author[0][0] if author else None
        return title, author
    except Exception as e:
        print(f"  ⚠️  No se pudieron leer metadatos EPUB de {filepath}: {e}")
        return None, None


def get_metadata_pdf(filepath):
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        info = reader.metadata
        title = info.title if info and info.title else None
        author = info.author if info and info.author else None
        return title, author
    except Exception as e:
        print(f"  ⚠️  No se pudieron leer metadatos PDF de {filepath}: {e}")
        return None, None


def get_metadata_mobi(filepath):
    try:
        import mobi
        tempdir, filepath_extracted = mobi.extract(filepath)
        # mobi devuelve la ruta del epub extraído; leemos sus metadatos
        return get_metadata_epub(filepath_extracted)
    except Exception as e:
        print(f"  ⚠️  No se pudieron leer metadatos MOBI de {filepath}: {e}")
        return None, None


def get_metadata(filepath, ext):
    if ext == ".epub":
        return get_metadata_epub(filepath)
    elif ext == ".pdf":
        return get_metadata_pdf(filepath)
    elif ext in (".mobi", ".azw3"):
        return get_metadata_mobi(filepath)
    return None, None


def build_new_filename(title, author, ext):
    """Construye el nuevo nombre de archivo a partir de autor y título."""
    if title and author:
        return f"{sanitize(author)} - {sanitize(title)}{ext}"
    elif title:
        return f"{sanitize(title)}{ext}"
    elif author:
        return f"{sanitize(author)}{ext}"
    return None


def rename_if_needed(books_dir, filename):
    """
    Intenta renombrar el archivo según sus metadatos.
    Devuelve el nombre de archivo final (renombrado o no).
    """
    ext = os.path.splitext(filename)[1].lower()
    filepath = os.path.join(books_dir, filename)

    title, author = get_metadata(filepath, ext)

    new_name = build_new_filename(title, author, ext)
    if not new_name or new_name == filename:
        return filename  # nada que cambiar

    # Evita colisiones añadiendo sufijo numérico si ya existe
    new_path = os.path.join(books_dir, new_name)
    if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(filepath):
        base, extension = os.path.splitext(new_name)
        counter = 1
        while os.path.exists(new_path):
            new_name = f"{base} ({counter}){extension}"
            new_path = os.path.join(books_dir, new_name)
            counter += 1

    os.rename(filepath, new_path)
    print(f"  📝 Renombrado: '{filename}' → '{new_name}'")
    return new_name


def generate():
    root = ET.Element("feed", attrib={
        "xmlns": FEED_NS,
        "xmlns:opds": OPDS_NS
    })
    ET.SubElement(root, "title").text = "Mi Biblioteca OPDS"
    ET.SubElement(root, "id").text = f"urn:uuid:mi-biblioteca-{int(datetime.datetime.now().timestamp())}"
    ET.SubElement(root, "updated").text = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    if not os.path.exists(BOOKS_DIR):
        os.makedirs(BOOKS_DIR, exist_ok=True)

    entries = []
    for f in sorted(os.listdir(BOOKS_DIR)):
        ext = os.path.splitext(f)[1].lower()
        if ext not in ALLOWED_EXT:
            continue

        # Renombrar según metadatos si es posible
        f = rename_if_needed(BOOKS_DIR, f)

        name = os.path.splitext(f)[0]
        url = f"books/{urllib.parse.quote(f)}"
        mime = MIME_MAP.get(ext, "application/octet-stream")

        entry = ET.SubElement(root, "entry")
        ET.SubElement(entry, "title").text = name
        ET.SubElement(entry, "id").text = f"urn:uuid:{f}"
        ET.SubElement(entry, "updated").text = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ET.SubElement(entry, "link", attrib={
            "href": url,
            "type": mime,
            "rel": "http://opds-spec.org/acquisition"
        })
        entries.append(f)

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"✅ feed.xml generado con {len(entries)} libros.")


if __name__ == "__main__":
    generate()
