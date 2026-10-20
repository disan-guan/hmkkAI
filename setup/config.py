
import configparser
from pathlib import Path

# config.ini berada satu folder di atas folder setup
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.ini"

config = configparser.ConfigParser()

if not CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"File konfigurasi tidak ditemukan: {CONFIG_PATH}"
    )

config.read(CONFIG_PATH, encoding="utf-8")

STREAM_URL = config.get("CCTV", "STREAM_URL")
MODEL_PATH = config.get("AI", "MODEL_PATH")

IMAGE_SIZE = config.getint("AI", "IMAGE_SIZE")
CONFIDENCE = config.getfloat("AI", "CONFIDENCE")
TARGET_FPS = config.getint("AI", "TARGET_FPS")

DISPLAY_WIDTH = config.getint("DISPLAY", "WIDTH")
DISPLAY_HEIGHT = config.getint("DISPLAY", "HEIGHT")
PANEL_ALPHA = config.getfloat("DISPLAY", "PANEL_ALPHA")

LINE_CENTER_X = config.getfloat("SENSOR", "CENTER_X")
LINE_CENTER_Y = config.getfloat("SENSOR", "CENTER_Y")
LINE_LENGTH = config.getfloat("SENSOR", "LENGTH")
LINE_ANGLE = config.getfloat("SENSOR", "ANGLE")

VEHICLES = {
    config.getint("VEHICLES", key): name
    for key, name in [
        ("MOBIL", "Mobil"),
        ("MOTOR", "Motor"),
        ("BUS", "Bus"),
        ("TRUK", "Truk"),
    ]
}
