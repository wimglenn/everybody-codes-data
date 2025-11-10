import pytest

from ecd import _impl


def test_get_token(fake_token):
    assert _impl.get_token() == fake_token


def test_get_token_env(monkeypatch):
    monkeypatch.setenv("ECD_TOKEN", "foo")
    assert _impl.get_token() == "foo"


def test_get_token_fail():
    with pytest.raises(_impl.EcdError, match="Couldn't find everybody-codes auth"):
        _impl.get_token()


def test_get_seed_cached(top, fake_seed):
    assert _impl.get_seed() == fake_seed


def test_get_seed_uncached(top, fake_token, pook):
    seed_path = top / "seed"
    assert not seed_path.exists()
    pook.get("https://everybody.codes/api/user/me").reply(200).json({"seed": 13})
    assert _impl.get_seed() == 13
    assert seed_path.read_text() == "13"
    seed_path.unlink()


def test_get_seed_fail(top, fake_token, pook):
    pook.get("https://everybody.codes/api/user/me").reply(400)
    err = _impl.EcdError("HTTP 400 from https://everybody.codes/api/user/me")
    with pytest.raises(err):
        _impl.get_seed()


def test_get_keys(fake_token, pook):
    url = "https://everybody.codes/api/event/2024/quest/1"
    pook.get(url).reply(200).json({"key1": "k"})
    result = _impl.get_keys(1, 2024)
    assert result == {"key1": "k"}


def test_get_keys_http_fail(fake_token, pook):
    url = "https://everybody.codes/api/event/2024/quest/1"
    pook.get(url).reply(400)
    err = _impl.EcdError(f"HTTP 400 from {url}")
    with pytest.raises(err):
        _impl.get_keys(1, 2024)


def test_get_keys_content_fail(fake_token, pook):
    url = "https://everybody.codes/api/event/2024/quest/1"
    pook.get(url).reply(200).json({"k": "v"})
    with pytest.raises(_impl.EcdError("failed to get keys")):
        _impl.get_keys(1, 2024)


def test_get_encrypted_inputs(fake_token, fake_seed, pook):
    url = "https://everybody-codes.b-cdn.net/assets/6/5/input/7.json"
    pook.get(url).reply(200).json({"x": "y"})
    result = _impl.get_encrypted_inputs(quest=5, event=6, seed=7)
    assert result == {"x": "y"}


def test_get_encrypted_inputs_fail(fake_token, fake_seed, pook):
    url = "https://everybody-codes.b-cdn.net/assets/6/5/input/7.json"
    pook.get(url).reply(400)
    with pytest.raises(_impl.EcdError(f"HTTP 400 from {url}")):
        _impl.get_encrypted_inputs(quest=5, event=6, seed=7)


def test_decoder():
    input_hex = "82db5c7f5b709666d261a0a041b1f80212ab50ff0646e35112e4c99810d7128c"
    key = "b^km1KO!&Yo?U9V0n8R=vm93Ax7Gif]6"
    expected = "17\n12\n7\n13\n17\n17\n19\n17\n10\n15\n16"
    assert _impl.decrypt(input_hex, key) == expected


def test_get_quest_and_event(mocker):
    fake_stack = [["bleh", "stuff"], ["ec2024/q01.py", "ecd"]]
    mocker.patch("traceback.extract_stack", return_value=fake_stack)
    assert _impl.get_quest_and_event() == (1, 2024)


def test_get_quest_and_event_fail(mocker):
    fake_stack = [["bleh", "stuff"], ["a/b.py", "ecd"]]
    mocker.patch("traceback.extract_stack", return_value=fake_stack)
    assert _impl.get_quest_and_event() == (None, None)


def test_get_http_with_proxy(monkeypatch, fake_token):
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.setenv("https_proxy", "https://test-proxy")
    http = _impl.get_http()
    assert http.proxy.host == "test-proxy"
    assert "everybody-codes-data" in http.headers["User-Agent"]
