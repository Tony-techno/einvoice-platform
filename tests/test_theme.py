import tomllib
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
KEYS = ("primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor")


def _is_hex_colour(value):
    return (
        isinstance(value, str)
        and len(value) == 7
        and value.startswith("#")
        and all(c in "0123456789abcdefABCDEF" for c in value[1:])
    )


def test_theme_has_light_and_dark_palettes():
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    for mode in ("light", "dark"):
        for key in KEYS:
            assert _is_hex_colour(theme[mode][key]), f"{mode}.{key} is not a valid colour"