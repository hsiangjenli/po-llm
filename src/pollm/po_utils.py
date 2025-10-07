import polib
import json


def load_po_file(file_path: str) -> str:
    """Load a PO file and return the polib POFile object as JSON string."""
    po = polib.pofile(file_path)
    po_dict = {
        "metadata": po.metadata,
        "header": po.header,
        "encoding": po.encoding,
        "entries": [e.__dict__ for e in po],
    }
    return json.dumps(po_dict)


def save_po_file(po_json: str, file_path: str) -> None:
    """Save the polib POFile object from JSON string to a file."""
    po_dict = json.loads(po_json)
    po = polib.POFile()
    po.metadata = po_dict["metadata"]
    po.header = po_dict["header"]
    po.encoding = po_dict["encoding"]
    for e_dict in po_dict["entries"]:
        entry = polib.POEntry(**e_dict)
        po.append(entry)
    po.save(file_path)