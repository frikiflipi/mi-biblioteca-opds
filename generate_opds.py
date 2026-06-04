#!/usr/bin/env python3
import os, urllib.parse, xml.etree.ElementTree as ET, datetime, mimetypes

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
