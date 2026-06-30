# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['obfuscated_src\\wec_visualisation\\main.py'],
    pathex=['obfuscated_src'],
    binaries=[],
    datas=[('C:\\Users\\gusta\\Desktop\\UU-WEC-visualisation\\.venv\\Lib\\site-packages\\customtkinter', 'customtkinter')],
    hiddenimports=['pyarmor_runtime_000000', 'wec_visualisation.config', 'wec_visualisation.main', 'wec_visualisation.gui.analytics', 'wec_visualisation.gui.app', 'wec_visualisation.gui.canvas', 'wec_visualisation.gui.components', 'wec_visualisation.gui.console', 'wec_visualisation.gui.language', 'wec_visualisation.gui.theme', 'wec_visualisation.models.environment', 'wec_visualisation.models.export', 'wec_visualisation.models.mission', 'wec_visualisation.models.simulation', 'wec_visualisation.models.turbine', 'wec_visualisation.snippets.capture_efficiency', 'customtkinter', 'tkinter', 'matplotlib', 'matplotlib.figure', 'matplotlib.backends.backend_tkagg', 'matplotlib.pyplot', 'numpy', 'numpy.polynomial', 'scipy', 'scipy.interpolate', 'scipy.special', 'scipy.optimize'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WEC_Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
