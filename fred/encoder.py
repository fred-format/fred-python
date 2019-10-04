from datetime import date, time, datetime
from functools import singledispatch
from itertools import chain
from json.encoder import py_encode_basestring_ascii as encode_string
from typing import Dict

import re

from .parser import TERMINALS
from .types import Symbol, Tag

#
# Regular expressions and other auxiliary constants
#
FRED_NAME = re.compile(TERMINALS["NAME"])
is_fred_name = FRED_NAME.fullmatch

# Construct
ESCAPE_BYTE_STRING: Dict[int, str] = {
    **{i: chr(i) for i in range(0x20, 0x7F)},
    b"\\"[0]: "\\\\",
    b"`"[0]: "\\`",
    b"\b"[0]: "\\b",
    b"\f"[0]: "\\f",
    b"\n"[0]: "\\n",
    b"\r"[0]: "\\r",
    b"\t"[0]: "\\t",
}
for i in range(0x20):
    ESCAPE_BYTE_STRING.setdefault(i, "\\x{0:02x}".format(i))
for i in range(0x7F, 0x100):
    ESCAPE_BYTE_STRING.setdefault(i, "\\x{0:02x}".format(i))


#
# Auxiliary encoding functions
#
def encode_byte_string(st):
    """
    Return a FRED representation of a Python string
    """
    data = ESCAPE_BYTE_STRING
    return "".join(chain("`", (data[i] for i in st), "`"))


def encode_symbol(symb, _is_name=is_fred_name, _encode=encode_string, _str=str):
    symb = _str(symb)
    if _is_name(symb):
        return f"${symb}"
    else:
        return f"${_encode(symb)}"


# Polymorphic encoders
class _EncodeError(Exception):
    """Private exception that tells encode_atom and encode_key have failed"""


def encode_key(obj, _is_name=is_fred_name, _encode=encode_string, _symb=Symbol):
    if isinstance(obj, str):
        return obj if _is_name(obj) else _encode(obj)
    elif obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif isinstance(obj, (int, float)):
        return _encode(str(obj))
    elif isinstance(obj, _symb):
        obj = str(obj)
        return obj if _is_name(obj) else _encode(obj)
    elif obj is None:
        return 'null'
    raise _EncodeError(f"cannot interpret {type(obj).__name__} as FRED key")


@singledispatch
def encode_atom(obj):
    raise _EncodeError(f"cannot convert {type(obj).__name__} to FRED")


# noinspection PyUnresolvedReferences
encode_simple = lambda cls, fn: encode_atom.register(cls)(fn)

encode_simple(type(None), lambda _: "null")
encode_simple(bool, lambda b: "true" if b else "false")
encode_simple(int, int.__repr__)
encode_simple(float, float.__repr__)
encode_simple(date, date.__str__)
encode_simple(time, time.__str__)
encode_simple(datetime, lambda x, _str=datetime.__str__: _str(x).replace(" ", "_"))
encode_simple(str, encode_string)
encode_simple(bytes, encode_byte_string)
encode_simple(Symbol, encode_symbol)


class FREDEncoder(object):
    """Extensible FRED <http://fred-format.org> encoder for Python data
    structures. The API is modelled after the builtin json.JSONEncoder.

    Supports the following objects and types by default:

    +-------------------+----------------+
    | Python            | JSON           |
    +===================+================+
    | dict              | object         |
    +-------------------+----------------+
    | list, tuple       | array          |
    +-------------------+----------------+
    | str               | string         |
    +-------------------+----------------+
    | bytes             | byte string    |
    +-------------------+----------------+
    | datetime.date     | time           |
    | datetime.time     |                |
    | datetime.datetime |                |
    +-------------------+----------------+
    | int, float        | number         |
    +-------------------+----------------+
    | fred.Symbol       | symbol         |
    +-------------------+----------------+
    | fred.Tag          | tagged element |
    +-------------------+----------------+
    | True              | true           |
    +-------------------+----------------+
    | False             | false          |
    +-------------------+----------------+
    | None              | null           |
    +-------------------+----------------+

    To extend this to recognize other objects, subclass and implement a
    ``.default()`` method with another method that returns a serializable
    object for ``o`` if possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).

    """

    item_separator = " "
    key_separator = ": "
    attr_separator = "="

    def __init__(
            self,
            *,
            skip_keys=False,
            ensure_ascii=True,
            check_circular=True,
            allow_nan=True,
            sort_keys=False,
            indent=None,
            separators=None,
            default=None,
            **kwargs,
    ):
        """Constructor for JSONEncoder, with sensible defaults.

        If skipkeys is false, then it is a TypeError to attempt
        encoding of keys that are not str, int, float or None.  If
        skipkeys is True, such items are simply skipped.

        If ensure_ascii is true, the output is guaranteed to be str
        objects with all incoming non-ASCII characters escaped.  If
        ensure_ascii is false, the output can contain non-ASCII characters.

        If check_circular is true, then lists, dicts, and custom encoded
        objects will be checked for circular references during encoding to
        prevent an infinite recursion (which would cause an OverflowError).
        Otherwise, no such check takes place.

        If allow_nan is true, then NaN, Infinity, and -Infinity will be
        encoded as such.  This behavior is not JSON specification compliant,
        but is consistent with most JavaScript based encoders and decoders.
        Otherwise, it will be a ValueError to encode such floats.

        If sort_keys is true, then the output of dictionaries will be
        sorted by key; this is useful for regression tests to ensure
        that JSON serializations can be compared on a day-to-day basis.

        If indent is a non-negative integer, then JSON array
        elements and object members will be pretty-printed with that
        indent level.  An indent level of 0 will only insert newlines.
        None is the most compact representation.

        If specified, separators should be an (item_separator, key_separator)
        tuple.  The default is (', ', ': ') if *indent* is ``None`` and
        (',', ': ') otherwise.  To get the most compact JSON representation,
        you should specify (',', ':') to eliminate whitespace.

        If specified, default is a function that gets called for objects
        that can't otherwise be serialized.  It should return a JSON encodable
        version of the object or raise a ``TypeError``.

        """
        if list(kwargs) == ['skipkeys']:
            raise TypeError('FREDEncoder uses skip_keys (mind the underscore)')
        elif kwargs:
            arg, _ = kwargs.popitem()
            raise TypeError(f'invalid argument: {arg}')

        self.skip_keys = skip_keys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.sort_keys = sort_keys
        self.indent = indent
        if separators is not None:
            self.item_separator, self.key_separator, self.attr_separator = separators
        elif indent is not None:
            self.item_separator = ""
        self._default = default or self.default

    def default(self, obj):
        """Implement this method in a subclass such that it returns
        a serializable object for ``obj``, or calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, obj):
                try:
                    iterable = iter(obj)
                except TypeError:
                    # Let the base class default method raise the TypeError
                    return super().default(obj)
                else:
                    return list(iterable)
        """
        msg = f"Object of type {type(obj).__name__} is not FRED serializable"
        raise TypeError(msg)

    def encode(self, obj):
        """
        Return a FRED string representation of a Python data structure.

        >>> from fred.encoder import FREDEncoder
        >>> FREDEncoder().encode({"foo": ["bar", "baz"]})
        '{foo: ["bar" "baz"]}'
        """
        return "".join(self.iterencode(obj, _one_shot=True))

    def iterencode(self, obj, _one_shot=False):
        """
        Encode the given object and yield each string representation as available.

        For example::

            for chunk in FREDEncoder().iterencode(bigobject):
                mysocket.write(chunk)
        """
        _iterencode = _make_iterencode(
            {} if self.check_circular else None,
            self._default,
            self.indent,
            self.key_separator,
            self.item_separator,
            self.sort_keys,
            self.skip_keys,
            _one_shot,
        )
        return _iterencode(obj, 0)


def _make_iterencode(
        markers,
        _default,
        _indent,
        _key_separator,
        _item_separator,
        _sort_keys,
        _skipkeys,
        _one_shot,
        _EncodeError=_EncodeError,
        dict=dict,
        id=id,
        sequence=(list, tuple),
        encode_atom=encode_atom,
):
    if _indent is not None and not isinstance(_indent, str):
        _indent = " " * _indent

    def encode_list(lst, _current_indent_level):
        if not lst:
            yield "[]"
            return

        if markers is not None:
            marker_id = id(lst)
            if marker_id in markers:
                raise ValueError("Circular reference detected")
            markers[marker_id] = lst

        buf = "["
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator

        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator

            try:
                yield buf + encode_atom(value)
            except _EncodeError:
                yield buf
                yield from encode_container(value, _current_indent_level)

        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + _indent * _current_indent_level
        yield "]"

        if markers is not None:
            # noinspection PyUnboundLocalVariable
            del markers[marker_id]

    def encode_dict(dic, _current_indent_level, empty="{}", left="{", right="}", sep=_key_separator):
        if not dic:
            yield empty
            return

        if markers is not None:
            marker_id = id(dic)
            if marker_id in markers:
                raise ValueError("Circular reference detected")
            markers[marker_id] = dic

        yield left
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator

        first = True
        if _sort_keys:
            items = sorted(dic.items(), key=lambda kv: kv[0])
        else:
            items = dic.items()

        for key, value in items:
            try:
                key = encode_key(key)
            except _EncodeError:
                if _skipkeys:
                    continue
                cls = type(key).__name__
                msg = f"keys must be str, int, float, bool or None, not {cls}"
                raise TypeError(msg)

            if first:
                first = False
            else:
                yield item_separator
            yield key
            yield sep

            try:
                yield encode_atom(value)
            except _EncodeError:
                yield from encode_container(value, _current_indent_level)

        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + _indent * _current_indent_level
        yield right

        if markers is not None:
            # noinspection PyUnboundLocalVariable
            del markers[marker_id]

    def encode_tag(tag_obj, _current_indent_level, is_name=FRED_NAME.fullmatch):
        tag, attrs, value = tag_obj.split()
        if not is_name(tag):
            tag = f'\\{encode_string(tag)}'

        if value is None:
            yield f'({tag}'
            if attrs:
                yield from encode_dict(attrs, _current_indent_level + 1, left=' ', right='', sep='=')
            yield ')'
        else:
            yield tag
            if attrs:
                yield from encode_dict(attrs, _current_indent_level + 1, left=' (', right=')', sep='=')
            yield ' '
            yield from encode_value(value, _current_indent_level)

    def encode_container(obj, indent, isinstance=isinstance):
        if isinstance(obj, sequence):
            yield from encode_list(obj, indent)
        elif isinstance(obj, dict):
            yield from encode_dict(obj, indent)
        elif isinstance(obj, Tag):
            yield from encode_tag(obj, indent)
        else:
            if markers is not None:
                marker_id = id(obj)
                if marker_id in markers:
                    raise ValueError("Circular reference detected")
                markers[marker_id] = obj
                obj = _default(obj)
                yield from encode_value(obj, indent)
                del markers[marker_id]
            else:
                obj = _default(obj)
                yield from encode_value(obj, indent)

    def encode_value(obj, indent):
        try:
            yield encode_atom(obj)
        except _EncodeError:
            yield from encode_container(obj, indent)

    return encode_value
