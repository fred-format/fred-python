from collections import namedtuple

from .context import Context
from .validators import make_validator
from .. import load, loads
from ..decoder import FREDDecoder
from ..types import Tag

SCHEMA_ERROR = ValueError
VALIDATION_ERROR = ValueError
INVALID_SCHEMA = SCHEMA_ERROR("invalid schema document")
TypeSchema = namedtuple("TypeSchema", ["id", "exported", "declarations"])


class Schema:
    """
    A validating FRED parser.
    """

    id: str
    exported: list
    declarations: dict

    def __init__(self, id: str, exported: list, declarations: dict, **kwargs):
        self.id = id
        self.exported = exported
        self.declarations = declarations
        self.decoder = FREDDecoder(**kwargs)
        self.validators = {}

        for decl in declarations.values():
            make_validator(decl, self.validators)

    def loads(self, src):
        """

        Args:
            src:

        Returns:

        """
        data = self.decoder.decode(src)
        return self.validate(data)

    def load(self, fd):
        """

        Args:
            data:

        Returns:

        """
        data = self.decoder.decode(fd.read())
        return self.validate(data)

    def validate(self, data):
        """
        Validate and normalize a parsed FRED structure.
        """
        tag, attrs, value = data.split()
        if tag not in self.exported:
            raise VALIDATION_ERROR(f"invalid root tag: {tag}")
        validator = self.validators[tag]
        ctx = Context()
        return validator(ctx, data)


def schema(data):
    """

    Args:
        data:

    Returns:

    """
    if isinstance(data, str):
        data = loads(data)
    elif not isinstance(data, Tag):
        data = load(data)
    return Schema(*parse_schema(data))


def parse_schema(scm: Tag) -> TypeSchema:
    """
    Check if a FRED structure represents a schema and return
    Args:
        scm:

    Returns:

    """
    if not isinstance(scm, Tag):
        raise INVALID_SCHEMA
    tag, attrs, value = scm.split()

    # Exported symbols
    head, *exported = tag.split("/")
    if head != "Schema" or not exported:
        raise SCHEMA_ERROR("root tag must be of the form Schema/(exported symbols)")

    # Meta attributes
    if list(attrs.keys()) != ["id"]:
        raise SCHEMA_ERROR("schema declaration requires an id attribute")
    id = attrs["id"]

    # Declarations
    if not isinstance(value, list):
        raise SCHEMA_ERROR(f"expected a list of declarations, got {value!r}")
    declarations = {}
    for decl in value:
        if not isinstance(decl, Tag):
            raise SCHEMA_ERROR(f"declarations should be tagged elements, got {decl!r}")
        declarations[decl.tag] = decl

    return TypeSchema(id, exported, declarations)
