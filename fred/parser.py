import datetime as dt
import re
from pathlib import Path

from lark import Lark, InlineTransformer
from lark.exceptions import UnexpectedInput

from .exceptions import FREDDecodeError

STRING_GRAMMAR_PATH = Path(__file__).parent / "grammar"

DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
TIME_RE = re.compile(
    r"([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.([0-9]{3}(?:[0-9]{3})?)?)?)?"
)
TIME_TZ_RE = re.compile(TIME_RE.pattern + r"([+-])([0-9]{2})(?::([0-9]{2}))?")
DATETIME_SPLIT_RE = re.compile(r"[T_]")

# Load grammar files and populate lists of terminal symbols
GRAMMAR_PATH = Path(__file__).parent / "grammar"
TERMINALS = {}

fred_grammar = Lark(open(GRAMMAR_PATH / "fred.lark"), parser="lalr", start="value")
for _decl in fred_grammar.terminals:
    TERMINALS[_decl.name] = _decl.pattern.to_regexp()

fn = staticmethod
cte = lambda x: lambda *args: x


# ==============================================================================
# String parsing
# ==============================================================================

def parse_string(tk) -> str:
    """
    Parse string using string parser.
    """
    try:
        return string_grammar.parse(tk)
    except UnexpectedInput as exc:
        msg = f"invalid string literal ({exc}), {tk}"
        raise FREDDecodeError.from_token(msg, tk)


def parse_byte_string(tk) -> bytes:
    """
    Parse byte string using byte string parser.
    """
    try:
        return byte_string_grammar.parse(tk)
    except UnexpectedInput as exc:
        msg = f"invalid byte string literal ({exc}), {tk}"
        raise FREDDecodeError.from_token(msg, tk)


class FredStringTransformer(InlineTransformer):
    """
    Parse FRED string.
    """

    def start(self, *args):
        return "".join(args)

    backspace = cte("\b")
    formfeed = cte("\f")
    newline = cte("\n")
    return_line = cte("\r")
    tab = cte("\t")
    quote = cte('"')
    backslash = cte("\\")
    solidus = cte("/")

    def unicode_extra(self, *args):
        return chr(int("".join(args), 16))

    def high(self, a, b, c):
        return int(a[-1] + b + c, 16) - 0x800

    def low(self, a, b, c):
        return int(a[-1] + b + c, 16) - 0xC00

    def surrogate_pair(self, high, low):
        return chr(high * 0x400 + low + 0x10000)

    def hex(self, a, b, c, d):
        return chr(int(a + b + c + d, 16))


class FredByteStringTransformer(InlineTransformer):
    """
    Parse FRED byte string.
    """

    def start(self, *args):
        return b"".join(args)

    backspace = cte(b"\b")
    formfeed = cte(b"\f")
    newline = cte(b"\n")
    return_line = cte(b"\r")
    tab = cte(b"\t")
    quote = cte(b"`")
    backslash = cte(b"\\")
    solidus = cte(b"/")

    def ascii(self, tk):
        return tk.encode("ascii")

    def hex(self, a, b):
        return bytes([int(a + b, 16)])


string_grammar = Lark(
    open(STRING_GRAMMAR_PATH / "string.lark"),
    parser="lalr",
    transformer=FredStringTransformer(),
)
byte_string_grammar = Lark(
    open(STRING_GRAMMAR_PATH / "byte_string.lark"),
    parser="lalr",
    transformer=FredByteStringTransformer(),
)


# ==============================================================================
# Dates and time parsing
# ==============================================================================

def _parse_date(st):
    return dt.date(*map(int, DATE_RE.fullmatch(st).groups()))


def _parse_time(st):
    groups = TIME_RE.fullmatch(st).groups()
    if groups[3] is not None:
        if len(groups[3]) == 3:
            groups = list(groups)
            groups[3] = groups[3] + "000"
    return dt.time(*(int(x) for x in groups if x is not None))


def _parse_time_tz(st):
    if st.endswith("Z"):
        hh, mm, ss, ms = TIME_RE.fullmatch(st[:-1]).groups()
        tz = dt.timezone.utc
    else:
        hh, mm, ss, ms, sign, tzhh, tzmm = TIME_TZ_RE.fullmatch(st).groups()

        # Use time to validate hour and minute ranges
        time = dt.time(int(tzhh), int(tzmm or 0))
        delta = dt.timedelta(hours=time.hour, minutes=time.minute)
        tz = dt.timezone(delta if sign == "+" else -delta)

    if ms and len(ms) == 3:
        ms = ms + "000"

    return dt.time(int(hh), int(mm), int(ss or 0), int(ms or 0), tz)


# Should we?
# if sys.version_info >= (3, 7):
#     _parse_date = dt.date.fromisoformat
#     _parse_time = dt.time.fromisoformat
#     _parse_datetime = lambda tk: dt.datetime.fromisoformat(tk.replace('T', '_'))


def parse_date(tk):
    """
    Return a date object from token.
    """
    try:
        return _parse_date(tk)
    except AttributeError:
        raise FREDDecodeError.from_token(f"invalid date literal, {tk}", tk)
    except ValueError as exc:
        raise FREDDecodeError.from_token(f"[date] {exc}", tk)


def parse_time(tk):
    try:
        return _parse_time(tk)
    except AttributeError:
        raise FREDDecodeError.from_token(f"invalid time literal, {tk}", tk)
    except ValueError as exc:
        raise FREDDecodeError.from_token(f"[time] {exc}", tk)


def parse_time_tz(tk):
    try:
        return _parse_time_tz(tk)
    except AttributeError:
        raise FREDDecodeError.from_token(f"invalid time literal, {tk}", tk)
    except ValueError as exc:
        raise FREDDecodeError.from_token(f"[time] {exc}", tk)


def parse_datetime(tk):
    date, time = DATETIME_SPLIT_RE.split(tk, 1)
    date = parse_date(date)
    time = parse_time(time)
    return dt.datetime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
        time.second,
        time.microsecond,
    )


def parse_datetime_tz(tk):
    date, time = DATETIME_SPLIT_RE.split(tk, 1)
    date = parse_date(date)
    time = parse_time_tz(time)
    return dt.datetime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
        time.second,
        time.microsecond,
        tzinfo=time.tzinfo,
    )
