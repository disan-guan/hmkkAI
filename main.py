
import subprocess
import sys
import time
from pathlib import Path

# Folder utama project
# BASE_DIR = Path(__file__).resolve().parent
# SETUP_DIR = BASE_DIR / "setup"
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

SETUP_DIR = BASE_DIR / "setup"
PYTHON = sys.executable

processes = {}


def start_process(name, script, args=None):
    script_path = SETUP_DIR / script

    if not script_path.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {script_path}"
        )

    command = [PYTHON, str(script_path)]

    if args:
        command.extend(args)

    process = subprocess.Popen(
        command,
        cwd=BASE_DIR
    )

    processes[name] = process
    print(f"[START] {name} berjalan (PID: {process.pid})")


def stop_all():
    print("\nMenghentikan semua proses...")

    for name, process in processes.items():
        if process.poll() is None:
            print(f"[STOP] {name}")
            process.terminate()

    for process in processes.values():
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    print("Semua proses dihentikan.")


def main():
    try:
        # Jalankan API
        start_process(
            "API",
            "api.py",
            ["--host", "0.0.0.0", "--port", "8000"]
        )

        time.sleep(2)

        # Jalankan AI Vehicle Counter
        start_process(
            "Vehicle Counter",
            "ai.py"
        )

        print("\nAI Vehicle Counter aktif.")
        print("API        : http://127.0.0.1:8000")
        print("Dokumentasi: http://127.0.0.1:8000/docs")
        print("Tekan CTRL+C untuk menghentikan program.\n")

        while True:
            for name, process in processes.items():
                if process.poll() is not None:
                    print(
                        f"[WARNING] {name} berhenti "
                        f"(exit code: {process.returncode})"
                    )

            time.sleep(2)

    except KeyboardInterrupt:
        pass

    except Exception as error:
        print(f"[ERROR] {error}")

    finally:
        stop_all()


if __name__ == "__main__":
    main()
