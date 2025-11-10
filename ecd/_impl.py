import logging
import os
import traceback
from functools import cache
from importlib.metadata import version
from pathlib import Path

import urllib3
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes


log = logging.getLogger(__name__)


top = Path("~/.config/ecd/").expanduser()
top.mkdir(parents=True, exist_ok=True)

v = version("everybody-codes-data")
user_agent = f"github.com/wimglenn/everybody-codes-data v{v} by hey@wimglenn.com"

url_seed = "https://everybody.codes/api/user/me"
url_keys = "https://everybody.codes/api/event/{event}/quest/{quest}"
url_post = "https://everybody.codes/api/event/{event}/quest/{quest}/part/{part}/answer"
url_data = "https://everybody-codes.b-cdn.net/assets/{event}/{quest}/input/{seed}.json"


class EcdError(Exception):
    pass


@cache
def get_token():
    val = os.environ.get("ECD_TOKEN")
    if val is not None:
        return val
    path = top / "token"
    if path.exists():
        return path.read_text().split()[0]
    raise EcdError(
        "Couldn't find everybody-codes auth token. Get the token from the browser "
        "cookie storage after signing in at https://everybody.codes/login."
    )


@cache
def get_http():
    token = get_token()
    headers = {
        "User-Agent": user_agent,
        "Cookie": f"everybody-codes={token}",
    }
    proxy_url = os.environ.get("http_proxy") or os.environ.get("https_proxy")
    if proxy_url:
        http = urllib3.ProxyManager(proxy_url, headers=headers)
    else:
        http = urllib3.PoolManager(headers=headers)
    return http


@cache
def get_seed():
    path = top / "seed"
    if path.is_file():
        seed = int(path.read_text())
        log.debug("got seed %d from memo %s", seed, path)
    else:
        http = get_http()
        resp = http.request("GET", url_seed)
        if resp.status != 200:
            raise EcdError(f"HTTP {resp.status} from {url_seed}")
        seed = resp.json()["seed"]
        path.write_text(str(seed))
        log.debug("wrote seed %d to memo %s", seed, path)
    return seed


def get_keys(quest, event):
    http = get_http()
    url = url_keys.format(quest=quest, event=event)
    resp = http.request("GET", url)
    if resp.status != 200:
        raise EcdError(f"HTTP {resp.status} from {url}")
    data = resp.json()
    if "key1" not in data:
        log.warning("unexpected response from %s:\n%s", url, data)
        raise EcdError("failed to get keys")
    return data


def get_encrypted_inputs(quest, event, seed):
    http = get_http()
    url = url_data.format(quest=quest, event=event, seed=seed)
    resp = http.request("GET", url)
    if resp.status != 200:
        raise EcdError(f"HTTP {resp.status} from {url}")
    data = resp.json()
    return data


def decrypt(input_hex, key):
    key_bytes = key.encode()
    iv = key_bytes[:16]
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    decryptor = cipher.decryptor()
    input_bytes = bytes.fromhex(input_hex)
    decrypted_bytes = decryptor.update(input_bytes) + decryptor.finalize()
    pad_length = decrypted_bytes[-1]
    result = decrypted_bytes[:-pad_length].decode()
    return result


valid_fnames = {f"q{n}.py" for n in range(1, 21)}
valid_fnames |= {f"q0{n}.py" for n in range(1, 10)}


def get_quest_and_event():
    # to use this introspection magic you must structure your files like ec2024/q01.py
    for frame in traceback.extract_stack():
        log.debug("ecd framesummary %s", frame)
        linetxt = frame[-1] or ""
        if "ecd" not in linetxt:
            continue
        fname = os.path.basename(frame[0])
        parent = os.path.basename(os.path.dirname(frame[0]))
        if fname in valid_fnames and parent.startswith("ec") and parent[2:].isdigit():
            quest = int(fname[1:-3])
            event = int(parent[2:])
            log.info("introspect quest=%d event=%d from frame=%s", quest, event, fname)
            return quest, event
    log.warning("failed to introspect quest/event")
    return None, None
