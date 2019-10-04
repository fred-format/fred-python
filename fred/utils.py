import datetime as dt

from .types import Symbol, Tag
from . import parser

INFINITY = float('inf')
NEG_INFINITY = float('-inf')
DECODERS = {
    'float': float,
    'date': parser.parse_date,
    'time': parser.parse_time,
    'datetime': parser.parse_datetime,
}

def json_encode(x):
    """
    Encode FRED data structure in JSON.
    """
    if isinstance(x, (str, int, bool)):
        return x
    elif x is None:
        return None
    elif isinstance(x, float):
        if x != x:
            return ["float", "nan"]
        elif x == INFINITY:
            return ["float", "inf"]
        elif x == NEG_INFINITY:
            return ["float", "-inf"]
        return x
    elif isinstance(x, dt.date):
        return ["date", str(x)]
    elif isinstance(x, dt.time):
        return ["time", str(x)]
    elif isinstance(x, dt.datetime):
        return ["datetime", str(x).replace(' ', 'T')]
    elif isinstance(x, Symbol):
        return ["symbol", str(x)]
    elif isinstance(x, Tag):
        attrs = {k: json_encode(v) for k, v in x.attrs.items()}
        return ["tag", x.tag, attrs, json_encode(x.value)]
    elif isinstance(x, (list, tuple)):
        return [list(map(json_encode, x))]
    elif isinstance(x, dict):
        return {str(k): json_encode(v) for k, v in x.items()}
    else:
        raise TypeError(f'invalid FRED type: {type(x).__name__}')


def json_decode(x):
    """
    Reverse the results of json_encode.
    """
    if isinstance(x, (str, int, bool, float)):
        return x
    elif x is None:
        return None
    elif isinstance(x, list):
        if isinstance(x[0], str):
            action, *args = x
            return DECODERS[action](*args)
        else:
            return list(map(json_decode, x[0]))
    elif isinstance(x, dict):
        return {k: json_decode(v) for k, v in x.items()}
    else:
        raise TypeError(f'invalid JSON type: {type(x).__name__}')
