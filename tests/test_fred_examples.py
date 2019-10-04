import math
from datetime import time, datetime, date, timezone, timedelta
from pathlib import Path
from pprint import pprint

import pytest

import fred
from fred import Symbol, Tag, lex, FREDDecodeError

repo = Path(__file__).parent.parent
examples = repo / "examples"


class TestSimpleExamples:
    def test_atomic(self):
        # Constants
        assert fred.loads('true') is True
        assert fred.loads('false') is False
        assert fred.loads('null') is None

        # Integers
        assert fred.loads('10') == 10
        assert fred.loads('-11') == -11
        assert fred.loads('0b10') == 2
        assert fred.loads('-0b11') == -3
        assert fred.loads('0o10') == 8
        assert fred.loads('-0o11') == -9
        assert fred.loads('0x10') == 16
        assert fred.loads('-0x11') == -17

        # Floats
        nan = fred.loads('nan')
        assert isinstance(nan, float) and nan != nan
        assert fred.loads('inf') == float('inf')
        assert fred.loads('-inf') == float('-inf')
        assert fred.loads('10.0') == 10.0
        assert fred.loads('-11.0') == -11.0
        assert fred.loads('1e1') == 10.0
        assert fred.loads('-1e1') == -10.0
        assert fred.loads('1.25e2') == 125.0
        assert fred.loads('1.25e-2') == 0.0125

        # Strings
        assert fred.loads('"abc"') == 'abc'
        assert fred.loads('"abc def"') == 'abc def'

    def test_string_lexing(self):
        assert fred.loads('""') == ''
        assert fred.loads('"abc"') == 'abc'
        assert fred.loads('"abc def"') == 'abc def'
        assert fred.loads(r'"abc\bdef"') == 'abc\bdef'
        assert fred.loads(r'"abc\fdef"') == 'abc\fdef'
        assert fred.loads(r'"abc\ndef"') == 'abc\ndef'
        assert fred.loads(r'"abc\rdef"') == 'abc\rdef'
        assert fred.loads(r'"abc\tdef"') == 'abc\tdef'
        assert fred.loads(r'"abc\"def"') == 'abc"def'
        assert fred.loads(r'"abc\\def"') == 'abc\\def'
        assert fred.loads(r'"abc\/def"') == 'abc/def'
        assert fred.loads(r'"\u00E1"') == 'á'
        assert fred.loads(r'"\u{E1}"') == 'á'
        assert fred.loads(r'"\uD801\uDC37"') == '\U00010437'
        assert fred.loads(r'"\uD834\uDD1E"') == '\U0001D11E'
        assert fred.loads(r'"\u{000000E1}"') == 'á'

    def test_byte_string_lexing(self):
        assert fred.loads('``') == b''
        assert fred.loads('`abc`') == b'abc'
        assert fred.loads('`abc def`') == b'abc def'
        assert fred.loads(r'`abc\bdef`') == b'abc\bdef'
        assert fred.loads(r'`abc\fdef`') == b'abc\fdef'
        assert fred.loads(r'`abc\ndef`') == b'abc\ndef'
        assert fred.loads(r'`abc\rdef`') == b'abc\rdef'
        assert fred.loads(r'`abc\tdef`') == b'abc\tdef'
        assert fred.loads(r'`abc\`def`') == b'abc`def'
        assert fred.loads(r'`abc\\def`') == b'abc\\def'
        assert fred.loads(r'`abc\/def`') == b'abc/def'
        assert fred.loads(r'`\x61`') == b'a'

    def test_parse_dates_and_times(self):
        assert fred.loads('2000-10-30') == date(2000, 10, 30)
        assert fred.loads('12:52:21.123') == time(12, 52, 21, 123000)
        assert fred.loads('12:32:21.123456') == time(12, 32, 21, 123456)
        assert fred.loads('2001-12-21_12:32:21.123456') == datetime(2001, 12, 21, 12, 32, 21, 123456)
        assert fred.loads('2001-12-21T12:32:21.123456') == datetime(2001, 12, 21, 12, 32, 21, 123456)
        assert fred.loads('12:32:21.123456Z') == time(12, 32, 21, 123456, timezone.utc)
        assert fred.loads('12:32:21.123+03:00') == time(12, 32, 21, 123000, timezone(timedelta(hours=3)))

    def test_enclosed_tag_parsing(self):
        src = '(tag)'
        assert list(lex(src)) == ['(', 'tag', ')']
        assert fred.loads(src) == Tag('tag')

        src = '(tag attr="value")'
        assert list(lex(src)) == ['(', 'tag', 'attr', '=', '"value"', ')']
        assert fred.loads(src) == Tag('tag', attr='value')

        src = '(tag $value)'
        assert list(lex(src)) == ['(', 'tag', '$value', ')']
        assert fred.loads(src) == Tag('tag', Symbol('value'))
        assert fred.loads('(tag "string")') == Tag('tag', 'string')

        src = '(tag attr="attr" $value)'
        assert list(lex(src)) == ['(', 'tag', 'attr', '=', '"attr"', '$value', ')']
        assert fred.loads(src) == Tag('tag', Symbol('value'), attr='attr')

        src = '(tag attr="attr" "value")'
        assert list(lex(src)) == ['(', 'tag', 'attr', '=', '"attr"', '"value"', ')']
        assert fred.loads(src) == Tag('tag', 'value', attr='attr')

    #
    # INVALID SYNTAX
    #
    @pytest.mark.parametrize('invalid', [r'"\x60"'])
    def test_invalid_strings(self, invalid):
        with pytest.raises(FREDDecodeError):
            fred.loads(invalid)

    @pytest.mark.parametrize('invalid', [r'`\u0060`'])
    def test_invalid_byte_strings(self, invalid):
        with pytest.raises(FREDDecodeError):
            fred.loads(invalid)

    @pytest.mark.parametrize('invalid', [
        r'1970-13-01',
        r'1970-1-1',
        r'10:5',
        r'10:50:21.12',
        r'10:60',
        r'10:60+3',
        r'10:60+03:60',
        r'10:60+24:00',
    ])
    def test_invalid_dates_and_times(self, invalid):
        with pytest.raises(FREDDecodeError):
            fred.loads(invalid)

    @pytest.mark.parametrize('invalid', [
        '[1 2 3',
        '{foo: bar'
    ])
    def test_invalid_syntax(self, invalid):
        with pytest.raises(FREDDecodeError):
            fred.loads(invalid)


class TestExampleFiles:
    def test_numbers_dot_fred(self):
        tag, meta, value = fred.load(examples / "numbers.fred").split()
        pprint(value)

        assert tag == 'Numbers'
        assert meta == {}
        assert value['int'] == [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assert value['float'] == [-1.0, 0.0, 1.0, 2.0, 3.1415, 42.0]
        assert value['bin'] == [-2, -1, 0, 1, 2, 5]
        assert value['octal'] == [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
        assert value['hex'] == [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16]

        nan, neg_inf, inf = value['literal']
        assert inf == float('inf')
        assert neg_inf == -float('inf')
        assert str(nan) == 'nan'

    def test_strings_dot_fred(self):
        tag, meta, value = fred.load(examples / "strings.fred").split()
        pprint(value)

        assert tag == 'Strings'
        assert meta == {}
        assert value['simple'] == ["abc", "abc def"]
        assert value['escaped'] == ["abc\ndef", "abc\tdef", 'abc"def']
        # assert value['single'] == "first line\nsecond line\nlast line"

    def test_full_dot_fred(self):
        tag, meta, value = fred.load(examples / "full.fred").split()
        pprint(value)

        assert tag == 'FRED/Full'
        assert meta == {}

        assert math.isnan(value["keywords"].pop(3))
        assert value["keywords"] == [True, False, None, float('inf'), -float('inf')]
        assert value["numbers"] == [0, -1, 2.0, -3.0, 4e+0, -5.0, 0b110, -0b111, 0o10, -0o11, 0xa, -0xb]
        assert value["strings"] == ["some string", 'with"escape"', b'some bytes', b'with`escape`']
        assert value["dates"] == [
            date(1970, 1, 1),
            time(12, 0),
            time(13, 0, tzinfo=timezone.utc),
            datetime(2001, 1, 1, 10, 32, tzinfo=timezone(timedelta(hours=3))),
        ]
        assert value["arrays"] == [[["nested"]], [[True]]]
        assert value["objects"] == [{"simple": True}, {"quoted": "ok"}]
        assert value["symbols"] == [
            Symbol('symbol'),
            Symbol("quoted symbol"),
            Symbol('dashed-case'), Symbol('name.space'), Symbol('main/variant')
        ]
        assert value["tags"] == [
            Tag('tag', ['tagged value'], attr='value'),
            Tag('enclosed-tag', 'tagged value', attr='value'),
            Tag('void-tag', attr1=1, attr2=2),
            Tag('void-tag'),
            Tag.new('tag', {'complex-attr': Tag('complex?', True), 'more...': [1, 2, 3]}, Symbol('simple-value')),
            Tag('nested', Tag('tag', Symbol('for-value'))),
            Tag.new('quoted tag', {'quoted attr': "value"}, {'tagged': "value"}),
        ]
