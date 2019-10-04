from typing import Tuple, Union, MutableMapping, Any
from weakref import WeakValueDictionary

SYMBOLS: MutableMapping[str, Any] = WeakValueDictionary()


class Symbol:
    """
    Symbols are unique representation of names.
    """

    _value: str

    @property
    def parts(self) -> Tuple["Symbol", ...]:
        return tuple(map(Symbol, self._value.split(".")))

    @property
    def base(self):
        data = self._value.rsplit(".", 1)[-1]
        return Symbol(data.split("/", 1)[0])

    @property
    def modifiers(self):
        data = self._value.rsplit(".", 1)[-1]
        return tuple(map(Symbol, data.split("/")[1:]))

    @classmethod
    def from_parts(cls, *parts) -> "Symbol":
        """
        Create symbol instance from a its parts.
        """
        return Symbol(".".join(map(_mk_part, parts)))

    def __new__(cls, value: str):
        try:
            return SYMBOLS[value]
        except KeyError:
            if not type(value) is str:
                raise TypeError("Symbol instances must be created from strings")
            symb = super().__new__(cls)
            symb._value = value
            SYMBOLS[value] = symb
            return symb

    def __repr__(self):
        return "Symbol(%r)" % self._value

    def __str__(self):
        return self._value

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self is other
        elif isinstance(other, str):
            return self._value == other
        return NotImplemented

    def __hash__(self):
        value = hash(self._value)
        return -1 if value == -1 else -value


SymbolS = Union[Symbol, str]


#
# Auxiliary functions
#
def _mk_part(x):
    return x if isinstance(x, str) else "/".join(x)
