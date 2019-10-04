import pytest
from hypothesis import given, example
from hypothesis import strategies as st

import fred
from fred import hypothesis as f
from fred import loads, dumps


class TestGrammar:
    pass


@pytest.mark.hypothesis
class TestParser:
    #
    # Round trips atomic values
    #
    @example('\x7f')
    @given(st.characters())
    def test_round_trip_strings(self, data):
        src = dumps(data)
        print(repr(src))
        assert loads(src) == data, src

    #
    # Composite FRED values
    #
    @given(f.fred_data().map(dumps))
    def test_encoder_produces_valid_fred_syntax(self, src):
        assert isinstance(loads(src), fred.decoder.FREDTypes)

    @given(f.fred_data(allow_nan=False))
    def test_round_trips_random_fred(self, data):
        src = dumps(data)
        assert loads(src) == data
