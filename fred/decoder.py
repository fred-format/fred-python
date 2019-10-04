from datetime import datetime, date, time
from typing import Union

from lark import InlineTransformer, UnexpectedToken

from .exceptions import FREDDecodeError
from . import parser
from .parser import (
    parse_string,
    parse_byte_string,
    parse_time,
    parse_datetime,
    parse_time_tz,
    parse_datetime_tz,
    fred_grammar,
)
from .types import Tag, Symbol

FREDTypes = Tag, list, dict, type(None), bool, float, int, str, Symbol, datetime, date, time
FRED = Union[Tag, list, dict, None, bool, float, int, str, Symbol, datetime, date, time]


class FREDDecoder(object):
    """Simple JSON <http://json.org> decoder

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | str               |
    +---------------+-------------------+
    | number (int)  | int               |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+

    It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.

    """
    object_pairs_hook = None
    object_hook = None
    attr_hook = None
    array_hook = None
    tag_hook = None
    parse_float = None
    parse_int = None

    def __init__(self, **kwargs):
        """``object_hook``, if specified, will be called with the result
        of every JSON object decoded and its return value will be used in
        place of the given ``dict``.  This can be used to provide custom
        deserializations (e.g. to support JSON-RPC class hinting).

        ``object_pairs_hook``, if specified will be called with the result of
        every JSON object decoded with an ordered list of pairs.  The return
        value of ``object_pairs_hook`` will be used instead of the ``dict``.
        This feature can be used to implement custom decoders.
        If ``object_hook`` is also defined, the ``object_pairs_hook`` takes
        priority.

        ``parse_float``, if specified, will be called with the string
        of every JSON float to be decoded. By default this is equivalent to
        float(num_str). This can be used to use another datatype or parser
        for JSON floats (e.g. decimal.Decimal).

        ``parse_int``, if specified, will be called with the string
        of every JSON int to be decoded. By default this is equivalent to
        int(num_str). This can be used to use another datatype or parser
        for JSON integers (e.g. float).
        """

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f'invalid argument: {k}')

        if self.object_pairs_hook is None and self.object_hook is not None:
            object_hook = self.object_hook
            object_pairs_hook = lambda pairs: object_hook(dict(pairs))
        else:
            object_pairs_hook = self.object_pairs_hook

        self.transformer = FREDTransformer(
            object_hook=object_pairs_hook,
            array_hook=self.array_hook,
            attr_hook=self.attr_hook,
            parse_int=self.parse_int,
            parse_float=self.parse_float,
        )

    def decode(self, src: str):
        """
        Return the Python representation of FRED source.

        """
        try:
            ast = fred_grammar.parse(src)
            return self.transformer.transform(ast)
        except UnexpectedToken as exc:
            tk = str(exc.token)
            msg = f"error in line {exc.line}, col {exc.column}. Unexpected {tk!r}"
            raise FREDDecodeError(msg, exc.line, exc.column)

    def raw_decode(self, src, idx=0):
        """
        Exists for compatibility with JSONDecoder.
        """
        msg = 'FRED decoder cannot parse documents with extraneous content.'
        raise NotImplementedError(msg)


#
# Lark Visitor/Transformer pattern
#
fn = staticmethod
cte = lambda x: lambda *args: x


class FREDTransformer(InlineTransformer):
    """
    FRED transformer.
    """

    # Literals
    true = cte(True)
    false = cte(False)
    null = cte(None)
    inf = cte(float("inf"))
    neg_inf = cte(-float("inf"))
    nan = cte(float("nan"))

    # Numbers
    int = int
    float = float
    bin = fn(lambda x: int(x, 2))
    oct = fn(lambda x: int(x, 8))
    hex = fn(lambda x: int(x, 16))

    # String-like
    string = fn(parse_string)
    byte_string = fn(parse_byte_string)
    symbol = fn(lambda x: Symbol(x[1:]))
    quoted_symbol = fn(lambda x: Symbol(parse_string(x[1:])))

    # Tags
    attr = pair = fn(lambda x, y: (x, y))
    attrs = lambda self, *args: self._attr_hook(args)
    name = fn(lambda x: x[:])
    name_escaped = fn(lambda x: parse_string(x[1:]))
    opt_value = fn(lambda value=None: value)

    def tag_inner(self, tag, *args):
        *args, value = args
        return self._tag_hook(tag, self._attr_hook(args), value)

    def tag_outer(self, tag, arg, *rest):
        if rest:
            return self._tag_hook(tag, arg, rest[0])
        return self._tag_hook(tag, {}, arg)

    # Dates and times
    date = lambda self, x: self._parse_date(x)
    time = fn(lambda x: parse_time(x))
    datetime = fn(lambda x: parse_datetime(x))
    time_tz = fn(lambda x: parse_time_tz(x))
    datetime_tz = fn(lambda x: parse_datetime_tz(x))

    # Data structures
    array = object = fn(lambda *xs: list(xs))
    array_single = object_single = fn(lambda x: [x])
    array_append = object_append = fn(lambda xs, x: xs.append(x) or xs)
    array_hook = lambda self, lst: self._array_hook(lst)
    object_hook = lambda self, lst: self._object_hook(lst)

    def __init__(self, object_hook=None, attr_hook=None, array_hook=None,
                 tag_hook=None,
                 parse_int=None, parse_float=None, parse_date=None,
                 parse_datetime=None, parse_time=None):
        self._object_hook = object_hook or dict
        self._attr_hook = attr_hook or self._object_hook
        self._array_hook = array_hook or list
        self._tag_hook = tag_hook or Tag.new

        if self._array_hook is list:
            self._array_hook = lambda x: x

        # Parsing functions
        self._parse_int = parse_int or int
        self._parse_float = parse_float or float
        self._parse_date = parse_date or parser.parse_date
        self._parse_datetime = parse_datetime or parser.parse_datetime
        self._parse_time = parse_time or parser.parse_time


del fn, cte
