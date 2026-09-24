from pathlib import Path


PROJECT_DIR = Path(".")


def collect_directory(directory):
    return [
        (str(path), str(path.parent))
        for path in directory.rglob("*")
        if path.is_file()
    ]


def collect_python_modules(directory):
    """
    Projedeki tüm .py dosyalarını Python modülü olarak toplar.
    """
    modules = []

    for path in directory.glob("*.py"):
        if path.name == "main2.py":
            continue

        modules.append(path.stem)

    return modules


datas = []


# --------------------------------------------------
# Asset klasörleri
# --------------------------------------------------

for directory in [
    PROJECT_DIR / "images",
    PROJECT_DIR / "musics",
    PROJECT_DIR / "settings_images",
    PROJECT_DIR / "screens",
]:
    datas += collect_directory(directory)


# --------------------------------------------------
# Tekil dosyalar
# --------------------------------------------------

for file in [
    "arabica.ttf",
    "notosans.ttf",
    "names",
    "securedvars",
    "settings",
    "settings.json",
    "public_key.pem",
]:
    path = PROJECT_DIR / file

    if path.is_file():
        datas.append((str(path), "."))


for file in [
    "basedir.py",
    "calcs.py",
    "classes.py",
    "colours.py",
    "console.py",
    "cooldown.py",
    "create_dirt.py",
    "dfont.py",
    "exceptions.py",
    "flags.py",
    "fonts.py",
    "gamedata.py",
    "game.py",
    "helper_funcs.py",
    "lang_support.py",
    "levels.py",
    "main2.py",
    "main.py",
    "pass_manager.py",
    "save_manager.py",
    "settings_manager.py",
    "settings.py",
    "typehint_game.py",
    "userfont.py",
    "zaman.py",
    "dump.py"
]:
    path = PROJECT_DIR / file

    if path.is_file():
        datas.append((str(path), "."))
    else:
        print(f"UYARI: Python dosyası bulunamadı: {path}")

# --------------------------------------------------
# Python modülleri
# --------------------------------------------------

hiddenimports = collect_python_modules(PROJECT_DIR)


# --------------------------------------------------
# Analysis
# --------------------------------------------------

a = Analysis(
    ["main2.py"],

    pathex=[
        str(PROJECT_DIR.resolve())
    ],

    binaries=[],

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[
        "tkinter",
    ],

    noarchive=False,
)


# --------------------------------------------------
# Python archive
# --------------------------------------------------

pyz = PYZ(
    a.pure
)


# --------------------------------------------------
# Executable
# --------------------------------------------------

exe = EXE(
    pyz,

    a.scripts,

    [],

    exclude_binaries=True,

    name="savas_oyunu1",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=True,
)


# --------------------------------------------------
# Final onedir package
# --------------------------------------------------

coll = COLLECT(
    exe,

    a.binaries,

    a.datas,

    a.zipfiles,

    strip=False,

    upx=True,

    name="main2",
)