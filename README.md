
# parrotjoy

For making music, and visuals.



## Get started.

```
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.dev.txt
python run_game.py

# record sounds and play them back with the joypad
python parrotjoy/looper.py

# make noises and watch circles appear.
parrotjoy/videosynth.py
```


### Running tests.

Tests can be found in the tests/ folder.

Type `pytest`.
Or run `python -m tox`

Tests are run on mac, linux, windows when there is a pull request made.

### releasing

Releasing is tested with python3.7(not python2 or any other version).

To the python package index (pypi).
```
rm -rf dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
```

On windows:
```
python setup.py bdist_msi
dir build/*.msi
```

On mac:
```
python setup.py bdist_dmg
ls build/*.dmg
```


## Licenses

#### Code license

License for code will be the same as the pygame license (LGPL, but you can keep your parts of course!)

