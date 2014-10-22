# -*- mode: python -*-

block_cipher = None


a = Analysis(
    ['barbacoa.py'],
    pathex=['BUILD/linux'],
    hiddenimports=['plugins.groovesync.groovesync', 'uuid', 'gzip', 'io', '_io'],
    hookspath=None,
    runtime_hooks=None,
    cipher=block_cipher
)

pyz = PYZ(
    a.pure,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    Tree('bbqlib', prefix='bbqlib'),
    Tree('plugins', prefix='plugins'),
    Tree('www', prefix='www'),
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='barbacoa',
    debug=False,
    strip=None,
    upx=True,
    console=False
)
