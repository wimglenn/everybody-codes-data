This library is used to decrypt input notes for [everybody.codes](https://everybody.codes/) events.

Your auth token should be placed at `~/.config/ecd/token`.
Get the token from the browser cookies storage after signing in at https://everybody.codes/login, it looks like a [UUID4](https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)) hex digest e.g. `1aa871d3-d271-4c6b-8178-7cf795bf995c`.
In Chrome, press F12 and then click the "Application" tab, and look for the cookie named `everybody-codes`.

To use `from ecd import data` magic, you must use file structure like `ec2024/q01.py` so that the library can introspect the event (2024) and quest (1) from the path name.
If you don't want to use such a directory structure, call the `ecd.get_inputs()` function directly instead of the import syntax.

The input data will only be cached locally once all three parts can be decrypted.
