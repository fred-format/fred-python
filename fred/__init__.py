"""
FRED (Flexible REpresentation of Data) is a simple text-based format that
extends JSON with some interesting capabilities.
"""
from json import detect_encoding
from pathlib import Path as _Path
from typing import Type as _Type, Iterator as _Iterator, Union as _Union

from lark import Token as _Token

from .decoder import FRED, FREDDecoder, fred_grammar as _grammar
from .encoder import FREDEncoder
from .exceptions import FREDDecodeError
from .types import Tag, FrozenTag, Symbol

__version__ = "0.1.0"


def dump(obj, fd=None, **kwargs):
    """
    Serialize ``obj`` to a FRED formatted stream using ``fd``'s write method.

    Args:
        obj:
            A FRED-serializable object.
        fd:
            A file descriptor.
        indent:
            Indentation for pretty-printed representations.
    """
    write = fd.write
    for chunk in FREDEncoder(**kwargs).iterencode(obj):
        write(chunk)


def dumps(obj, **kwargs) -> str:
    """
    Serialize ``obj`` to a FRED formatted string.

    Args:
        obj:
            A FRED-serializable object.
    """
    return FREDEncoder(**kwargs).encode(obj)


def load(fd, **kwargs) -> FRED:
    """
    Load FRED data from a file-like object.

    Args:
        fd:
            A file-like object that stores a FRED document.
    """

    if isinstance(fd, (str, _Path)):
        with open(fd) as fd:
            return load(fd, **kwargs)
    else:
        return loads(fd.read(), **kwargs)


def loads(src: _Union[str, bytes], cls: _Type[FREDDecoder] = None, **kwargs) -> FRED:
    """
    Load FRED data from string.

    Args:
        src:
            A string with FRED formatted text.
        cls:
            A FREDEncoder subclass.
        object_hook:
            Used to construct objects.
    """
    if isinstance(src, str):
        if src.startswith('\ufeff'):
            msg = "Unexpected UTF-8 BOM (decode using utf-8-sig)"
            raise FREDDecodeError(msg, 0, 0)
    else:
        if not isinstance(src, (bytes, bytearray)):
            cls_name = type(src).__name__
            msg = f'the JSON object must be str, bytes or bytearray, not {cls_name}'
            raise TypeError(msg)
        src = src.decode(detect_encoding(src), 'surrogatepass')

    dec = (cls or FREDDecoder)(**kwargs)
    return dec.decode(src)


def lex(src: str) -> _Iterator[_Token]:
    """
    Return an iterator over tokens of a FRED document.
    """
    return _grammar.lex(src)
