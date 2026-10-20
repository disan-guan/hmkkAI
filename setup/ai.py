import cv2
import time
import math
from collections import defaultdict
from ultralytics import YOLO
from database import save_event, get_summary, now_local
from config import (
    STREAM_URL,
    MODEL_PATH,
    IMAGE_SIZE,
    CONFIDENCE,
    TARGET_FPS,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    LINE_CENTER_X,
    LINE_CENTER_Y,
    LINE_LENGTH,
    LINE_ANGLE,
    PANEL_ALPHA,
    VEHICLES,
)

# =========================
# INISIALISASI
# =========================

print("Memuat model YOLO...")
model = YOLO(MODEL_PATH)

print("Menghubungkan CCTV...")
cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Gagal terhubung ke CCTV.")
    raise SystemExit

counter = defaultdict(
    lambda: {"Masuk": 0, "Keluar": 0}
)

counter_date = now_local().strftime("%Y-%m-%d")

# Muat rekap hari ini dari SQLite saat program dijalankan
today_summary = get_summary(counter_date)

for vehicle_name, values in today_summary["vehicles"].items():
    counter[vehicle_name]["Masuk"] = values["Masuk"]
    counter[vehicle_name]["Keluar"] = values["Keluar"]

# Posisi sebelumnya: ID -> (x, y, class_id)
previous_positions = {}

# ID yang sudah dihitung
counted_ids = set()

# FPS
previous_frame_time = time.perf_counter()
fps_actual = 0.0

print("CCTV terhubung.")
print(f"Target FPS: {TARGET_FPS}")
print("Tekan Q untuk keluar.")

# =========================
# MEMBUAT GARIS SENSOR
# =========================

def get_sensor_line(width, height):
    cx = int(width * LINE_CENTER_X)
    cy = int(height * LINE_CENTER_Y)

    length = int(width * LINE_LENGTH)
    angle = math.radians(LINE_ANGLE)

    dx = int((length / 2) * math.cos(angle))
    dy = int((length / 2) * math.sin(angle))

    p1 = (cx - dx, cy - dy)
    p2 = (cx + dx, cy + dy)

    return p1, p2


# =========================
# MENENTUKAN SISI GARIS
# =========================

def get_line_side(point, p1, p2):
    return (
        (p2[0] - p1[0]) * (point[1] - p1[1])
        - (p2[1] - p1[1]) * (point[0] - p1[0])
    )


# =========================
# CEK PERPOTONGAN DUA SEGMEN
# =========================

def segments_intersect(p, q, a, b):
    """
    Memeriksa apakah lintasan kendaraan p -> q
    memotong segmen garis sensor a -> b.
    """

    rx = q[0] - p[0]
    ry = q[1] - p[1]

    sx = b[0] - a[0]
    sy = b[1] - a[1]

    denominator = rx * sy - ry * sx

    # Lintasan sejajar atau hampir sejajar
    if abs(denominator) < 1e-9:
        return False

    qpx = a[0] - p[0]
    qpy = a[1] - p[1]

    t = (qpx * sy - qpy * sx) / denominator
    u = (qpx * ry - qpy * rx) / denominator

    # Kedua titik potong harus berada di dalam segmen
    return (
        0.0 <= t <= 1.0
        and 0.0 <= u <= 1.0
    )


# =========================
# GAMBAR GARIS DAN LABEL SISI
# =========================

def draw_sensor_line(frame, p1, p2):
    cv2.line(
        frame,
        p1,
        p2,
        (0, 255, 255),
        3,
        cv2.LINE_AA
    )

    # Titik ujung garis
    cv2.circle(frame, p1, 7, (255, 0, 255), -1)
    cv2.circle(frame, p2, 7, (255, 0, 255), -1)

    cv2.putText(
        frame,
        "A",
        (p1[0] + 8, p1[1] - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 255),
        2
    )

    cv2.putText(
        frame,
        "B",
        (p2[0] + 8, p2[1] - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 255),
        2
    )

    # Tentukan posisi label pada kedua sisi garis
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)

    if length > 0:
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2

        # Normal menuju sisi positif
        nx = -dy / length
        ny = dx / length

        offset = 35

        # Sisi positif = sisi Masuk
        masuk_x = int(mid_x + nx * offset)
        masuk_y = int(mid_y + ny * offset)

        # Sisi negatif = sisi Keluar
        keluar_x = int(mid_x - nx * offset)
        keluar_y = int(mid_y - ny * offset)

        cv2.putText(
            frame,
            "SISI DALAM",
            (masuk_x, masuk_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "SISI LUAR",
            (keluar_x, keluar_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 120, 255),
            2
        )


# =========================
# PANEL COUNTER
# =========================


def draw_counter(frame, counter, fps_actual, target_fps, date_text):

    x1, y1 = 20, 20
    x2, y2 = 440, 365

    overlay = frame.copy()

    cv2.rectangle(
        overlay, (x1, y1), (x2, y2), (25, 25, 25), -1
    )

    cv2.addWeighted(
        overlay, PANEL_ALPHA, frame, 1 - PANEL_ALPHA, 0, frame
    )

    cv2.rectangle(
        frame, (x1, y1), (x2, y2), (0, 200, 255), 2
    )

    cv2.putText(
        frame, "AI VEHICLE COUNTER",
        (35, 55), cv2.FONT_HERSHEY_SIMPLEX,
        0.8, (0, 220, 255), 2
    )

    # Tanggal
    cv2.putText(
        frame, f"Tanggal: {date_text}",
        (35, 88), cv2.FONT_HERSHEY_SIMPLEX,
        0.65, (255, 255, 255), 2
    )

    cv2.putText(
        frame, f"FPS: {fps_actual:.1f} / Target: {target_fps}",
        (35, 120), cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (255, 255, 255), 2
    )

    cv2.putText(
        frame, "Jenis",
        (35, 155), cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (200, 200, 200), 2
    )

    cv2.putText(
        frame, "Masuk",
        (190, 155), cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (0, 255, 0), 2
    )

    cv2.putText(
        frame, "Keluar",
        (305, 155), cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (0, 120, 255), 2
    )

    row_y = 195

    for vehicle_name in VEHICLES.values():
        masuk = counter[vehicle_name]["Masuk"]
        keluar = counter[vehicle_name]["Keluar"]

        cv2.putText(
            frame, vehicle_name,
            (35, row_y), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (255, 255, 255), 2
        )

        cv2.putText(
            frame, str(masuk),
            (215, row_y), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (0, 255, 0), 2
        )

        cv2.putText(
            frame, str(keluar),
            (330, row_y), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (0, 120, 255), 2
        )

        row_y += 40

    return frame



# =========================
# LOOP UTAMA
# =========================

frame_interval = 1.0 / TARGET_FPS

try:
    while True:

        loop_start = time.perf_counter()

        # Deteksi pergantian tanggal berdasarkan waktu Jakarta
        current_date = now_local().strftime("%Y-%m-%d")

        if current_date != counter_date:
            counter_date = current_date
            counter.clear()

            # Muat rekap untuk tanggal baru
            today_summary = get_summary(counter_date)

            for vehicle_name, values in today_summary["vehicles"].items():
                counter[vehicle_name]["Masuk"] = values["Masuk"]
                counter[vehicle_name]["Keluar"] = values["Keluar"]

            # ID tracking baru mungkin digunakan setelah pergantian hari
            counted_ids.clear()
            previous_positions.clear()

        # Hitung FPS aktual
        elapsed = loop_start - previous_frame_time

        if elapsed > 0:
            instant_fps = 1.0 / elapsed

            if fps_actual == 0:
                fps_actual = instant_fps
            else:
                fps_actual = (
                    0.8 * fps_actual
                    + 0.2 * instant_fps
                )

        previous_frame_time = loop_start

        ret, frame = cap.read()

        if not ret:
            print("Gagal membaca frame CCTV.")
            time.sleep(1)
            continue

        original_height, original_width = frame.shape[:2]

        # Hitung koordinat sensor berdasarkan resolusi asli
        line_p1, line_p2 = get_sensor_line(
            original_width,
            original_height
        )

        # Deteksi dan tracking kendaraan
        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=list(VEHICLES.keys()),
            conf=CONFIDENCE,
            imgsz=IMAGE_SIZE,
            device="cpu",
            verbose=False
        )

        annotated_frame = frame.copy()

        # Gambar sensor virtual
        draw_sensor_line(
            annotated_frame,
            line_p1,
            line_p2
        )

        if results and results[0].boxes is not None:

            for box in results[0].boxes:

                if box.id is None:
                    continue

                vehicle_id = int(box.id[0])
                class_id = int(box.cls[0])

                vehicle_name = VEHICLES.get(class_id)

                if vehicle_name is None:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                # Titik bawah tengah kendaraan
                center_x = (x1 + x2) // 2
                center_y = y2

                current_point = (center_x, center_y)

                # Gambar kotak kendaraan
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    annotated_frame,
                    f"{vehicle_name} ID {vehicle_id}",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # Titik pelacakan
                cv2.circle(
                    annotated_frame,
                    current_point,
                    5,
                    (0, 0, 255),
                    -1
                )

                previous_data = previous_positions.get(
                    vehicle_id
                )

                if previous_data is not None:

                    previous_x, previous_y, previous_class = (
                        previous_data
                    )

                    # Hanya proses jika kelas kendaraan sama
                    if (
                        previous_class == class_id
                        and vehicle_id not in counted_ids
                    ):

                        previous_point = (
                            previous_x,
                            previous_y
                        )

                        previous_side = get_line_side(
                            previous_point,
                            line_p1,
                            line_p2
                        )

                        current_side = get_line_side(
                            current_point,
                            line_p1,
                            line_p2
                        )

                        # Harus benar-benar melintasi segmen garis
                        crossed = (
                            previous_side * current_side < 0
                            and segments_intersect(
                                previous_point,
                                current_point,
                                line_p1,
                                line_p2
                            )
                        )

                        if crossed:
                            direction = None

                            if previous_side < 0 and current_side > 0:
                                direction = "Masuk"

                            elif previous_side > 0 and current_side < 0:
                                direction = "Keluar"

                            if direction:
                                try:
                                    # Simpan kejadian ke SQLite terlebih dahulu
                                    event = save_event(
                                        vehicle_type=vehicle_name,
                                        direction=direction,
                                        vehicle_id=vehicle_id
                                    )

                                    # Tambahkan ke panel hanya jika penyimpanan berhasil
                                    counter[vehicle_name][direction] += 1
                                    counted_ids.add(vehicle_id)

                                    print(
                                        f"{event['event_time']} | "
                                        f"{vehicle_name} | {direction} | "
                                        f"ID {vehicle_id} | "
                                        f"Total: {counter[vehicle_name][direction]}"
                                    )

                                except Exception as e:
                                    print(f"Gagal menyimpan data kendaraan: {e}")

                # Simpan posisi untuk frame berikutnya
                previous_positions[vehicle_id] = (
                    center_x,
                    center_y,
                    class_id
                )

        # Resize hanya untuk tampilan
        display_frame = cv2.resize(
            annotated_frame,
            (DISPLAY_WIDTH, DISPLAY_HEIGHT),
            interpolation=cv2.INTER_AREA
        )

        # Panel tetap berukuran konsisten
        display_frame = draw_counter(
            display_frame,
            counter,
            fps_actual,
            TARGET_FPS,
            counter_date
        )

        cv2.imshow(
            "AI Vehicle Counter",
            display_frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # Batasi laju pemrosesan
        processing_time = (
            time.perf_counter() - loop_start
        )

        remaining_time = (
            frame_interval - processing_time
        )

        if remaining_time > 0:
            time.sleep(remaining_time)

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Program CCTV dihentikan.")