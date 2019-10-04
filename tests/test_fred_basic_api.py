from fred import Symbol, loads, load
import pytest
import io


class TestLoading:
    def test_can_load_from_bytes(self):
        assert loads(b'42') == 42
        assert load(io.BytesIO(b'42')) == 42

    def test_detect_invalid_encoding_in_documents(self):
        with pytest.raises(ValueError):
            loads('\ufeff[1 2 3]')

        with pytest.raises(TypeError):
            loads(Symbol('42'))
