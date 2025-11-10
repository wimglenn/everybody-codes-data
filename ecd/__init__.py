import json
import logging
import sys
import typing as t

from urllib3 import BaseHTTPResponse

from . import _impl
from . import cli


_log = logging.getLogger(__name__)


def get_inputs(*, quest: int, event: int, seed: int | None = None) -> dict[str, str]:
    """Get decrypted inputs for the given quest/event. The event (e.g. 2024) and the
    quest (1-20) must be specified by keyword argument, to avoid any ambiguity. The
    inputs will be retrieved from a local cache if it exists, but not that the cache
    will be written only once all three parts can be decrypted.
    """
    if seed is None:
        seed = _impl.get_seed()
    fname = f"{event}-{quest:02d}.{seed}.json"
    path = _impl.top / fname
    if path.is_file():
        result = json.loads(path.read_text())
        _log.debug("got inputs from memo %s", path)
        return result
    keys = _impl.get_keys(quest, event)
    encrypted_inputs = _impl.get_encrypted_inputs(quest, event, seed)
    result = {}
    for k, v in encrypted_inputs.items():
        if f"key{k}" in keys:
            result[k] = _impl.decrypt(v, keys[f"key{k}"])
    if result.keys() >= {"1", "2", "3"}:
        serialized = json.dumps(result, indent=2)
        path.write_text(serialized)
        _log.debug("wrote %d bytes to memo %s", len(serialized), path)
    return result


def submit(
    *,
    quest: int,
    event: int,
    part: t.Literal[1, 2, 3],
    answer: int | str,
    quiet: bool = False,
) -> BaseHTTPResponse:
    """Submit answer for the given quest/event. All arguments are keyword-only. Part
    should be 1, 2, or 3."""
    http = _impl.get_http()
    url = _impl.url_post.format(quest=quest, event=event, part=part)
    _log.info("submitting %s to %s", answer, url)
    resp = http.request("POST", url, json={"answer": answer})
    if resp.status == 200:
        data = resp.json()
        pretty = json.dumps(data, indent=2)
        if data.get("correct"):
            _log.info("CORRECT: %s", pretty)
            if not quiet:
                print(f"Submitted {answer} to {url} and got:\n{pretty}")
        else:
            _log.warning("INCORRECT: %s", pretty)
    elif resp.status == 409:
        msg = f"HTTP {resp.status} - was the correct answer already submitted?"
        if resp.data:
            msg += "\n" + resp.data.decode(errors="replace")
        _log.info(msg)
        if not quiet:
            print(f"Submitted {answer} to {url} and got", msg)
    elif resp.status == 423:  # locked
        _log.warning("HTTP %d - was a bad answer submitted too recently?", resp.status)
    else:
        _log.warning("HTTP %d: %s", resp.status, resp.data.decode(errors="replace"))
    return resp


def __getattr__(name: str) -> t.Any:
    if name == "data":
        quest, event = _impl.get_quest_and_event()
        if event is None:
            return
        result = get_inputs(quest=quest, event=event)
        return result
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# prevent the import statement `from ecd import data` from going into
# importlib._bootstrap._handle_fromlist, which causes __getattr__ to be called twice
# see https://discuss.python.org/t/module-getattr-invoked-twice-importlib-bug/25600
del sys.modules[__name__].__path__
