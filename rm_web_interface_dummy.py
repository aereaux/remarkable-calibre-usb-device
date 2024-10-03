# %%
from enum import Enum
import mimetypes
import uuid
import io
import dataclasses
import json
from urllib import request, parse as urllib_parse


IP = "10.11.99.1"
base_url = f"http://{IP}"
HEADERS__CONTENT_TYPE__JSON = {"Content-Type": "application/json"}
HEADERS__CHARSET__ISO88591 = {"charset": "ISO-8859-1"}


# %%
class TypeOfDocument(str, Enum):
    DocumentType = "DocumentType"
    CollectionType = "CollectionType"


@dataclasses.dataclass
class Document:
    # Bookmarked
    # CurrentPage': 6,
    ID: str
    #'ModifiedClient': '2024-09-26T20:25:19.379Z',
    Parent: str
    Type: str
    VissibleName: str
    fileType: str

    @classmethod
    def parse(cls, d: dict):
        return Document(
            d["ID"],
            d["Parent"],
            d.get("Type"),
            d.get("VissibleName", ""),  # .encode("ISO-8859-1").decode("utf-8"),
            d.get("fileType"),
        )


@dataclasses.dataclass
class Node:
    children: list["ChildNode"] = dataclasses.field(default_factory=list)

    def ls_recursive(self: "Node"):
        result = []
        for c in self.children:
            if c.document.Type == TypeOfDocument.CollectionType:
                ls_children = list(map(lambda path: f"{c.visible_name}/{path}", c.ls_recursive()))
                result.extend(ls_children)
            else:
                result.append(c.visible_name)
        return result


@dataclasses.dataclass
class ChildNode(Node):
    document: Document = None

    @property
    def visible_name(self):
        return self.document.VissibleName


class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # Use a large random byte string to separate
        # parts of the MIME data.
        self.boundary = ("------" + uuid.uuid4().hex).encode("utf-8")
        return

    def get_content_type(self):
        return "multipart/form-data; boundary={}".format(self.boundary.decode("utf-8"))

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self.files.append((fieldname, filename, mimetype, body))
        return

    @staticmethod
    def _form_data(name):
        return ('Content-Disposition: form-data; name="{}"\r\n').format(name).encode("utf-8")

    @staticmethod
    def _attached_file(name, filename):
        return (
            # ('Content-Disposition: file; name="{}"; filename="{}"\r\n')
            ('Content-Disposition: form-data; name="{}"; filename="{}"\r\n').format(name, filename).encode("utf-8")
        )

    @staticmethod
    def _content_type(ct):
        return "Content-Type: {}\r\n".format(ct).encode("utf-8")

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()
        boundary = b"--" + self.boundary + b"\r\n"

        # Add the form fields
        for name, value in self.form_fields:
            buffer.write(boundary)
            buffer.write(self._form_data(name))
            buffer.write(b"\r\n")
            buffer.write(value.encode("utf-8"))
            buffer.write(b"\r\n")

        # Add the files to upload
        for f_name, filename, f_content_type, body in self.files:
            buffer.write(boundary)
            buffer.write(self._attached_file(f_name, filename))
            buffer.write(self._content_type(f_content_type))
            buffer.write(b"\r\n")
            buffer.write(body)
            buffer.write(b"\r\n")

        buffer.write(b"--" + self.boundary + b"--\r\n")
        return buffer.getvalue()


# %%


def query_document(path_id, **kwargs):
    headers = {}
    headers.update(HEADERS__CONTENT_TYPE__JSON)
    headers.update(HEADERS__CHARSET__ISO88591)
    url = f"{base_url}/documents/{path_id}"
    req = request.Request(url)
    for k, v in headers.items():
        req.add_header(k, v)
    with request.urlopen(req, **kwargs) as conn:
        return json.loads(conn.read())


def upload_file(filename, filepath, **kwargs):
    pass


def check_connection():
    return True


def query_tree(path_id):
    root = Node()
    return root


# %%
def upload(files: list[str], names: list[str]):
    for f, n in zip(files, names):
        upload_file(f, n)
