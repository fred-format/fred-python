import io
from datetime import date, time, datetime

import pytest

from fred import dumps, Tag, Symbol, dump


class TestFileDump:
    def test_dump_to_file(self):
        fd = io.StringIO()
        dump('value', fd)
        assert fd.getvalue() == '"value"'


class TestFredEncoder:

    def test_dump_primitive_types(self):
        # Constants
        assert dumps(True) == 'true'
        assert dumps(False) == 'false'
        assert dumps(None) == 'null'
        assert dumps(float('nan')) == 'nan'
        assert dumps(float('inf')) == 'inf'
        assert dumps(-float('inf')) == '-inf'

        # Numeric
        assert dumps(0) == '0'
        assert dumps(42) == '42'
        assert dumps(-42) == '-42'
        assert dumps(42_000) == '42000'

        assert dumps(0.0) == '0.0'
        assert dumps(42.0) == '42.0'
        assert dumps(-42.0) == '-42.0'
        assert dumps(42e20) == '4.2e+21'

        assert dumps(date(1970, 1, 1)) == '1970-01-01'
        assert dumps(time(12, 59)) == '12:59:00'
        assert dumps(datetime(1970, 1, 1, 12, 59)) == '1970-01-01_12:59:00'

        # String-like
        assert dumps('string') == '"string"'
        assert dumps(b'bytes') == '`bytes`'
        assert dumps(Symbol('symbol')) == '$symbol'
        assert dumps(Symbol('escaped symbol')) == '$"escaped symbol"'

    def test_list_encoder(self):
        assert dumps([]) == '[]'
        assert dumps([1, 2, 3, 4]) == '[1 2 3 4]'
        assert dumps([[]]) == '[[]]'
        assert dumps([{}]) == '[{}]'

    def test_dict_encoder(self):
        assert dumps({}) == '{}'
        assert dumps({"foo": "bar"}) == '{foo: "bar"}'
        assert dumps({"foo": "bar", "ham": "eggs"}) == '{foo: "bar" ham: "eggs"}'
        assert dumps({"dict": {}}) == '{dict: {}}'
        assert dumps({"list": []}) == '{list: []}'

    def test_key_encoder(self):
        assert dumps({
            42: 42,
            3.14: 3.14,
            True: True,
            False: False,
            None: None,
            Symbol('foo'): Symbol('foo'),
            Symbol('foo bar'): Symbol('foo bar')
        }) == '{"42": 42 "3.14": 3.14 true: true false: false null: null foo: $foo "foo bar": $"foo bar"}'

        with pytest.raises(TypeError):
            dumps({1 + 2j: 'value'})

    def test_tag_encoder(self):
        assert dumps(Tag('Tag', True)) == 'Tag true'
        assert dumps(Tag('Complex Tag', True)) == r'\"Complex Tag" true'
        assert dumps(Tag('Tag', [1, 2, 3])) == 'Tag [1 2 3]'
        assert dumps(Tag('Tag', [1, 2, 3], foo=1, bar=2)) == 'Tag (foo=1 bar=2) [1 2 3]'
        assert dumps(Tag.new('Tag', {'key with space': True}, None)) == '(Tag "key with space"=true)'

    def test_default(self):
        assert dumps([1 + 2j], default=str) == '["(1+2j)"]'
        assert dumps([1 + 2j], default=str, check_circular=False) == '["(1+2j)"]'

        with pytest.raises(TypeError):
            dumps([1 + 2j])

    def test_circular_dependencies_check(self):
        with pytest.raises(ValueError):
            dumps(1 + 2j, default=lambda x: [x])

        with pytest.raises(ValueError):
            a = []
            a.append(a)
            dumps(a)

        with pytest.raises(ValueError):
            a = {}
            a["self"] = a
            dumps(a)

    def test_key_options(self):
        assert dumps({1+2j: "complex"}, skip_keys=True) == '{}'
        assert dumps({"b": "last", "a": "first"}, sort_keys=True) == '{a: "first" b: "last"}'

    def test_decoder_arguments(self):
        with pytest.raises(TypeError) as err:
            dumps("value", bad_argument=True)
        assert str(err.value) == 'invalid argument: bad_argument'

        with pytest.raises(TypeError) as err:
            dumps("value", skipkeys=True)
        assert str(err.value) == 'FREDEncoder uses skip_keys (mind the underscore)'

    def test_indented_decoder(self):
        assert dumps([{'foo': 42, 'bar': {'ham': 'spam'}}], indent=4) == EXAMPLE_1



EXAMPLE_1 = '''[
    {
        foo: 42
        bar: {
            ham: "spam"
        }
    }
]'''
