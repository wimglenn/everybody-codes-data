import json
import logging

import ecd


def test_getattr(mocker):
    mocker.patch("ecd._impl.get_quest_and_event", return_value=(1, 2))
    mock_get_inputs = mocker.patch("ecd.get_inputs", return_value="test data")
    assert ecd.data == "test data"
    mock_get_inputs.assert_called_once_with(quest=1, event=2)


def test_getattr_null(mocker):
    mocker.patch("ecd._impl.get_quest_and_event", return_value=(None, None))
    assert ecd.data is None


def test_get_inputs_cached(top):
    cached = top / "2-01.3.json"
    cached.write_text('{"k":"v"}')
    actual = ecd.get_inputs(quest=1, event=2, seed=3)
    assert actual == {"k": "v"}


def test_get_inputs_uncached(top, mocker):
    seed_mock = mocker.patch("ecd._impl.get_seed", return_value=4)
    keys_mock = mocker.patch("ecd._impl.get_keys")
    keys_mock.return_value = {"key1": "k1", "key2": "k2", "key3": "k3"}
    get_mock = mocker.patch("ecd._impl.get_encrypted_inputs")
    get_mock.return_value = {"1": "encrypted1", "2": "encrypted2", "3": "encrypted3"}
    mocker.patch("ecd._impl.decrypt", lambda s, k: f"decrypted-{k}")
    cached = top / "2-01.4.json"
    actual = ecd.get_inputs(quest=1, event=2)
    assert actual == {"1": "decrypted-k1", "2": "decrypted-k2", "3": "decrypted-k3"}
    assert json.loads(cached.read_text()) == actual
    cached.unlink()
    seed_mock.assert_called_once()


def test_get_inputs_no_cache_for_partial_unlock(top, mocker, fake_seed):
    keys_mock = mocker.patch("ecd._impl.get_keys")
    keys_mock.return_value = {"key1": "k1"}
    get_mock = mocker.patch("ecd._impl.get_encrypted_inputs")
    get_mock.return_value = {"1": "encrypted1", "2": "encrypted2", "3": "encrypted3"}
    mocker.patch("ecd._impl.decrypt", lambda s, k: f"decrypted-{k}")
    cached = top / "2-01.82.json"
    actual = ecd.get_inputs(quest=1, event=2)
    assert actual == {"1": "decrypted-k1"}
    assert not cached.exists()


def test_submit(fake_token, pook, capsys):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(200).json({"correct": True})
    resp = ecd.submit(quest=1, event=2, part=3, answer=4)
    out, err = capsys.readouterr()
    assert not err
    assert '"correct": true' in out
    assert resp.json() == {"correct": True}


def test_submit_quiet(fake_token, pook, capsys):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(200).json({"correct": True})
    resp = ecd.submit(quest=1, event=2, part=3, answer=4, quiet=True)
    out, err = capsys.readouterr()
    assert not err
    assert not out
    assert resp.json() == {"correct": True}


def test_submit_incorrect(fake_token, pook, caplog):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(200).json({"correct": False})
    resp = ecd.submit(quest=1, event=2, part=3, answer=4)
    assert resp.json() == {"correct": False}
    assert "INCORRECT" in caplog.text


def test_submit_409(fake_token, pook, caplog):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(409)
    with caplog.at_level(logging.INFO):
        resp = ecd.submit(quest=1, event=2, part=3, answer=4, quiet=True)
    assert resp.status == 409
    assert "was the correct answer already submitted?" in caplog.text


def test_submit_409_extra(fake_token, pook, capsys):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(409).body("foo")
    resp = ecd.submit(quest=1, event=2, part=3, answer=4)
    assert resp.status == 409
    out, err = capsys.readouterr()
    assert not err
    assert "foo" in out


def test_submit_423(fake_token, pook, caplog):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(423)
    resp = ecd.submit(quest=1, event=2, part=3, answer=4)
    assert resp.status == 423
    assert "was a bad answer submitted too recently?" in caplog.text


def test_submit_fail(fake_token, pook, caplog):
    url = "https://everybody.codes/api/event/2/quest/1/part/3/answer"
    pook.post(url).reply(400).body("uh-oh")
    resp = ecd.submit(quest=1, event=2, part=3, answer=4)
    assert resp.status == 400
    assert "HTTP 400: uh-oh" in caplog.text
