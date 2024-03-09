# YakYak Developer Notes

Python setup
> pip install wheel
> pip install build
> pip install twine

Purge generated content:  
> rm -rf build/ dist/ yakyak/yakyak_makermattdesign.egg-info

Generate repository artifacts  
> python setup.py bdist_wheel sdist
> python3 -m build
 
Upload the package to the PyPi test server
> twine upload -r testpypi dist/*

Upload final version to PyPi server
> twine upload dist/*

