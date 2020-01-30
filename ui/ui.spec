# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files
import pyqtlet
import os

version = '1.6.6'

osgeo_binaries = collect_data_files('osgeo', include_py_files=True)

block_cipher = None

binaries = []
for p, lib in osgeo_binaries:
    if '.pyd' in p:
        binaries.append((p, '.'))

a = Analysis(['ui.py', 'ui.spec'],
             pathex=['.'],
             binaries=binaries,
             datas=[(os.path.dirname(pyqtlet.__file__), 'pyqtlet'),
                    (os.environ['PROJ_LIB'], 'proj')],
             runtime_hooks=['hook.py'],
             excludes=[],
             hiddenimports=['pkg_resources.py2_warn'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

name = 'SHETran-Results-Viewer-{}'.format(version)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name,
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name=name)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=name,
          upx=False,
          strip=False,
          console=False,
          debug=False)
