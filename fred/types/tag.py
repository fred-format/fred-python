import re
from types import MappingProxyType
from typing import Mapping, Tuple, Any, Pattern

from .symbol import Symbol, SymbolS

ATOMIC_VALUE_KEY_ERROR = "cannot access key of atomic value"
ATOMIC_VALUE_LEN_ERROR = "atomic value does not have length"


class Tag:
    """
    A tagged value associates a symbol and optional dictionary of meta
    information to any value.
    """

    __slots__ = "_tag", "_value", "_attrs"

    tag = property(lambda self: self._tag)
    value = property(lambda self: self._value)
    attrs = property(lambda self: self._attrs)

    _tag: str
    _value: Any
    _attrs: dict
    _FRED_NAME_RE: Pattern

    @classmethod
    def new(cls, tag: SymbolS, attrs: Mapping, value: object):
        """
        Create a new Tagged object from tag, an attribute dictionary and a
        value.

        Args:
            tag (Symbol or str):
                A symbol or string representing the tag.
            attrs (mapping):
                Mapping from attribute names to the corresponding values.
                If attrs is *not* a dictionary, it will be converted to a
                regular Python dictionary. Otherwise it will be assigned without
                a copy.
            value:
                The tagged object. It can be any Python value.
        """
        tagged = object.__new__(cls)
        return tagged.__init(tag, attrs, value)

    def __init__(self, tag: SymbolS, value=None, **kwargs):
        kwargs = {k.replace("_", "-"): v for k, v in kwargs.items()}
        self.__init(tag, kwargs, value)

    def __init(self, tag, attrs, value):
        if isinstance(tag, (str, Symbol)):
            tag = str(tag)
        else:
            raise TypeError("tag must be a string or Symbol.")

        self._tag = tag
        self._attrs = attrs
        self._value = value
        return self

    def __repr__(self):
        name = self.__class__.__name__
        kwargs = ""
        if self.attrs:
            kwargs = ", " + ", ".join("%s=%r" % p for p in self._attrs.items())
        value = "" if self._value is None else ", %r" % self._value
        return "%s(%r%s%s)" % (name, self._tag, value, kwargs)

    def __str__(self):
        tag = self._tag
        attrs = self._attrs
        value = self._value
        if not self._is_valid_fred_name(tag):
            tag = f"\\{tag!r}"

        if value is None and not attrs:
            return "(%s)" % tag
        elif value is None:
            kwargs = " ".join("%s=%r" % p for p in attrs.items())
            return "(%s %s)" % (tag, kwargs)
        else:
            kwargs = ""
            if attrs:
                kwargs = " ".join("%s=%r" % p for p in attrs.items())
                kwargs = " (%s)" % kwargs
            return "%s%s %r" % (tag, kwargs, value)

    def __getitem__(self, item):
        self._check_string()
        return self._value[item]

    def __len__(self):
        self._check_string()
        return len(self._value)

    def __iter__(self):
        self._check_string()
        return iter(self._value)

    def __eq__(self, other):
        if isinstance(other, Tag):
            return (
                    self._tag == other._tag
                    and self._value == other._value
                    and self._attrs == other._attrs
            )
        return NotImplemented

    @staticmethod
    def _is_valid_fred_name(st: str) -> bool:
        try:
            regex = Tag._FRED_NAME_RE
        except AttributeError:
            from ..parser import TERMINALS

            regex = Tag._FRED_NAME_RE = re.compile(TERMINALS["NAME"])
        return bool(regex.fullmatch(st))

    def _check_string(self):
        if isinstance(self._value, str):
            raise ValueError(ATOMIC_VALUE_KEY_ERROR)

    def split(self) -> Tuple[str, dict, Any]:
        """
        Return an iterator over the tag, attrs, value elements. This is useful
        to deconstruct the tag element as in the example:

        >>> tag, attrs, value = Tag('div', 'Hello').split()
        >>> tag, attrs, value
        ('div', {}, 'Hello')
        """
        return self._tag, self._attrs, self._value

    def retag(self, tag, unsafe=False):
        """
        Return a copy of tag with a new tag value.
        """
        return Tag.new(tag, self._attrs, self._value)


class FrozenTag(Tag):
    """
    Immutable Tagged object
    """

    __slots__ = ("_hash",)
    attrs = property(lambda self: MappingProxyType(self._attrs))

    def __hash__(self):
        try:
            h = self._hash
            if h == -1:
                raise TypeError
            return h
        except AttributeError:
            items = self._attrs.items()
            try:
                self._hash = hash((self._tag, self._value, *items))
            except TypeError:
                self._hash = -1
                raise
            return self._hash
