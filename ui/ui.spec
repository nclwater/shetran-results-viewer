# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files
import pyqtlet
import os

version = '1.6.4'

osgeo_binaries = collect_data_files('osgeo', include_py_files=True)

block_cipher = None

binaries = []
for p, lib in osgeo_binaries:
    if '.pyd' in p:
        binaries.append((p, '.'))

a = Analysis(['ui.py', 'ui.spec'],
             pathex=['.'],
             binaries=binaries,
             datas=[(os.path.dirname(pyqtlet.__file__), 'pyqtlet')],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
#
# libs = [
#     'mkl',
#     'libopenblas'
# ]


# def remove_from_list(b, keys):
#     out = []
#     for item in b:
#         n, _, _ = item
#         flag = 0
#         for key_word in keys:
#             if n.find(key_word) > -1:
#                 flag = 1
#         if flag != 1:
#             out.append(item)
#     return out
#
#
# a.binaries = remove_from_list(a.binaries, libs)

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
