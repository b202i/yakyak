# YakYak Developer Notes

Python setup
```bash
pip install wheel
pip install build
pip install twine
```

Purge generated content:  
```bash
rm -rf build/ dist/ yakyak.egg-info/
```

Generate repository artifacts  
```bash
python3 -m build
```
 
Upload the package to the PyPi test server.
```bash
twine upload -r testpypi dist/*
```
Note that when testing with the test.pypi.org server, it might not have wyoming or soundfile. You will need to install these first from the standard pypi.org server.
```bash
pip install wyoming
pip install soundfile
pip install -i https://test.pypi.org/simple/ yakyak==1.6.3
```

Upload final version to PyPi server
```bash
twine upload dist/*
```

## Upgrade Packages with PIP
List outdated packages
```bash
pip list --outdated                                                 
```
Update outdated packages
```bash
pip install --upgrade $(pip list --outdated | awk 'NR>2 {print $1}')
```
