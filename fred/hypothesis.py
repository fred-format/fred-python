from hypothesis import strategies as st

from .types import Symbol, Tag

undots = lambda x: None if x is ... else x


def extract_kwargs(kwargs, *args):
    return {arg: kwargs[arg] for arg in args if arg in kwargs}


def fred_atom(**kwargs):
    return st.one_of(
        st.floats(**extract_kwargs(kwargs, 'allow_nan', 'allow_infinite')),
        st.characters(),
        st.integers(),
        st.booleans(),
        st.just(None),
        st.dates(),
        st.datetimes(),
        st.times(),
        st.characters().map(Symbol)
    )


def fred_tagged(tag=None, value=None, attrs=None):
    value = undots(value) or fred_atom()
    attrs = undots(attrs) or st.dictionaries(fred_keys(), value)
    tag = undots(tag) or st.characters()
    return st.builds(Tag.new, tag, attrs, value)


def fred_data(depth=0, **kwargs):
    if depth <= 0:
        atom = fred_atom(**kwargs)
    else:
        atom = fred_data(depth=depth - 1, **kwargs)
    return st.one_of(
        atom,
        st.lists(atom),
        st.dictionaries(fred_keys(), atom),
        fred_tagged(..., atom)
    )


def fred_keys():
    return st.text()
