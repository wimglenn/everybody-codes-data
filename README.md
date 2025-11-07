[![pypi](https://img.shields.io/pypi/v/everybody-codes-data.svg)](https://pypi.org/project/everybody-codes-data/)
[![actions](https://github.com/wimglenn/everybody-codes-data/actions/workflows/test.yml/badge.svg)](https://github.com/wimglenn/everybody-codes-data/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/wimglenn/everybody-codes-data/branch/main/graph/badge.svg)](https://app.codecov.io/gh/wimglenn/everybody-codes-data)
![womm](https://cdn.rawgit.com/nikku/works-on-my-machine/v0.2.0/badge.svg)


# Everybody Codes Data

This library is used to decrypt input notes for [everybody.codes](https://everybody.codes/) events.


## Install

``` bash
pip install everybody-codes-data
```


## Auth

Your auth token should be placed at `~/.config/ecd/token` or defined in the `ECD_TOKEN` environment variable.
Get the token from the browser cookie storage after signing in at https://everybody.codes/login.
It looks like a [UUID4](https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)) hex digest, e.g. `1aa871d3-d271-4c6b-8178-7cf795bf995c`.
In Chrome, when you're on [the website](https://everybody.codes/) press F12 and then click the "Application" tab, and look for the cookie named `everybody-codes`.


## Usage

There is a getter function `ecd.get_inputs` which accepts the quest and event, and returns a dict of your decrypted data.
The dict will have string keys "1", "2", "3" corresponding to the puzzle parts.
Inputs are unlocked as you complete subsequent parts, so the dict will have only the key "1" initially.

``` python
>>> from ecd import get_inputs
>>> data = get_inputs(quest=3, event=2024)
>>> print(data["1"])
..............................
..............................
.............#................
.............##.#...#.........
..........#.#####...###.......
..........#########.#.........
.........############.........
.........##############.......
.........#############........
..........##.###.##...........
...........#...#.#............
...........#..................
..............................
..............................
```

There is also a CLI:

``` bash
$ ecd 3 2024 --part 1
..............................
..............................
.............#................
.............##.#...#.........
..........#.#####...###.......
..........#########.#.........
.........############.........
.........##############.......
.........#############........
..........##.###.##...........
...........#...#.#............
...........#..................
..............................
..............................
```

See `ecd --help` for more info on that.


## Submission

`everybody-codes-data` can also post answers.

``` python
from ecd import submit
submit(quest=1, event=2024, part=1, answer=1323)
```

If you don't want the submission result printed to the terminal, pass `quiet=True`.

The result of the submission will be logged (so you may want to [configure the logging framework](https://docs.python.org/3/howto/logging.html#configuring-logging) in your project), but if you want to see the result explicitly the return value here is just a [`urllib3.HTTPResponse`](https://urllib3.readthedocs.io/en/stable/reference/urllib3.response.html#response) instance.

``` python
from ecd import submit
result = submit(quest=1, event=2024, part=1, answer=1323, quiet=True)
print(result.status)
print(result.json())
```


## Import interface

There is also a "magic" interface, similar to [advent-of-code-data](https://github.com/wimglenn/advent-of-code-data), where you can use a direct import statement.
To use this feature, you must structure your directories and filenames like `ec{event}/q{quest}.py` in order that the library can introspect the event/quest from the path.
For example, this structure should work:

```
my-repo/ec2024/q01.py    (event=2024, quest=1) 
my-repo/ec2024/q02.py    (event=2024, quest=2)
my-repo/ec2025/q01.py    (event=2025, quest=1)
```

Then in your script, the dict of data will be populated from an import statement:

``` python
from ecd import data
```

If you don't want to use this directory structure, call the `ecd.get_inputs()` function directly instead of using the import syntax. The getter function has no restrictions on script, module or package names.


## Caching

This library will cache inputs to avoid hitting the server unnecessarily.
Your input data will only be cached locally once all three parts can be decrypted (i.e. once you've solved part 1 and part 2).
There is no caching for partial solves.
Caches are stored at `~/.config/ecd` in JSON format, they can be safely removed anytime.
