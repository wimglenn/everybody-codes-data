import pytest

from ecd import _impl


@pytest.fixture(autouse=True)
def clear_caches():
    yield
    _impl.get_token.cache_clear()
    _impl.get_http.cache_clear()
    _impl.get_seed.cache_clear()


@pytest.fixture(autouse=True)
def top(tmp_path, mocker):
    mocker.patch("ecd._impl.top", tmp_path)
    yield tmp_path


@pytest.fixture
def fake_token(top):
    path = top / "token"
    val = "1aa871d3-d271-4c6b-8178-7cf795bf995c"
    path.write_text(val)
    yield val
    path.unlink()


@pytest.fixture
def fake_seed(top):
    path = top / "seed"
    val = 82
    path.write_text(str(val))
    yield val
    path.unlink()
