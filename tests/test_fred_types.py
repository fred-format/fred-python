import pickle

import pytest

from fred import Tag, Symbol, FrozenTag, FREDDecodeError


class TestSymbolType:
    def test_constructor(self):
        assert Symbol('foo') is Symbol('foo')
        assert Symbol.from_parts('foo', 'bar') is Symbol('foo.bar')
        assert Symbol.from_parts(('foo', 'mod'), ('bar', 'mod')) is Symbol('foo/mod.bar/mod')

    def test_invalid_constructions(self):
        with pytest.raises(TypeError):
            print(Symbol(42))

        with pytest.raises(TypeError):
            print(Symbol(b'foo'))

    def test_parts(self):
        assert Symbol('foo.bar').parts == ('foo', 'bar')
        assert Symbol('foo/mod.bar/mod').parts == ('foo/mod', 'bar/mod')

        fst, snd = Symbol('foo/mod.bar/mod').parts
        assert fst.base == 'foo'
        assert fst.modifiers == ('mod',)
        assert snd.base == 'bar'
        assert snd.modifiers == ('mod',)

    def test_equality_with_different_types(self):
        assert Symbol('foo') == Symbol('foo')
        assert Symbol('foo') == 'foo'
        assert Symbol('foo') != b'foo'


class TestTagType:
    def test_constructor(self):
        assert Tag('foo') == Tag(Symbol('foo'))
        assert type(Tag(Symbol('foo')).tag) is str
        assert Tag.new('foo bar', {}, None).tag == 'foo bar'

    def test_invalid_constructions(self):
        with pytest.raises(TypeError):
            Tag(42)

    def test_equality(self):
        assert Tag('foo') == Tag('foo')
        assert Tag('foo') != Tag('bar')
        assert Tag('foo', 'bar') == Tag('foo', 'bar')
        assert Tag('foo', 'bar', baz='baz') == Tag('foo', 'bar', baz='baz')
        assert Tag('foo') != 'foo'

    def test_basic_interface(self):
        assert str(Tag('foo')) == '(foo)'
        assert str(Tag('foo bar')) == r"(\'foo bar')"
        assert str(Tag('foo', bar=42)) == '(foo bar=42)'
        assert str(Tag('foo', 'bar')) == "foo 'bar'"
        assert str(Tag('foo', 'bar', baz=42)) == "foo (baz=42) 'bar'"
        assert repr(Tag('foo')) == "Tag('foo')"
        assert repr(Tag('foo', bar=42)) == "Tag('foo', bar=42)"
        assert repr(Tag('foo', 'bar', baz=42)) == "Tag('foo', 'bar', baz=42)"

    def test_behaves_like_dict(self):
        dic = {'foo': 1, 'bar': 2}
        tag = Tag('Dic', dic)
        assert len(tag) == 2
        assert tag['foo'] == dic['foo']
        assert list(tag) == ['foo', 'bar']

    def test_behaves_like_list(self):
        lst = [1, 2, 3]
        tag = Tag('Dic', lst)
        assert len(tag) == 3
        assert tag[0] == lst[0]
        assert list(tag) == [1, 2, 3]

    def test_treat_string_as_atomic(self):
        tag = Tag('foo', 'bar')
        with pytest.raises(ValueError):
            print(len(tag))
        with pytest.raises(ValueError):
            print(list(tag))
        with pytest.raises(ValueError):
            print(tag[0])

    def test_frozen_tags(self):
        tag = FrozenTag('foo', 'bar')

        with pytest.raises(TypeError):
            tag.attrs['foo'] = 'bar'

    def test_frozen_tags_hashes(self):
        tag = FrozenTag('foo', 'bar')

        assert hash(tag) != -1
        assert tag.__hash__() is tag.__hash__()

    def test_invalid_hashes_for_non_hashable_value(self):
        with pytest.raises(TypeError):
            tag = FrozenTag('foo', {})
            print(hash(tag))

        assert tag._hash == -1
        with pytest.raises(TypeError):
            print(hash(tag))


class TestExceptionType:
    def test_constructor(self):
        # TODO: define messages and interfaces.
        exc = FREDDecodeError('msg', 1, 2)

    def test_pickle(self):
        exc = FREDDecodeError.from_token('msg', 'tk')
        clone = pickle.loads(pickle.dumps(exc))
        assert clone.__dict__ == exc.__dict__
        assert str(clone) == str(exc)
