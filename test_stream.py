
import cv2
import time

URL = (
    "https://stream.serangkota.go.id/LiveApp/streams/"
    "serangtimur.m3u8"
    "?token=undefined&subscriberId=undefined&subscriberCode=undefined"
)

TARGET_FPS = 25
RECONNECT_AFTER = 10

def open_stream():
    cap = cv2.VideoCapture(URL, cv2.CAP_FFMPEG)

    if cap.isOpened():
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    cap.release()
    return None


cap = open_stream()

if cap is None:
    print("Gagal membuka stream CCTV.")
    raise SystemExit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("CCTV Serang Timur")
print(f"FPS sumber : {fps}")
print(f"Resolusi   : {width} x {height}")
print("Tekan Q untuk keluar.")

last_frame_time = time.time()
frame_count = 0
fps_start = time.time()
display_fps = 0

try:
    while True:
        loop_start = time.time()

        ret, frame = cap.read()

        if ret:
            last_frame_time = time.time()
            frame_count += 1

            # Hitung FPS tampilan aktual
            elapsed_fps = time.time() - fps_start

            if elapsed_fps >= 1:
                display_fps = frame_count / elapsed_fps
                frame_count = 0
                fps_start = time.time()

            cv2.putText(
                frame,
                f"Source FPS: {fps:.1f}",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Display FPS: {display_fps:.1f}",
                (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Resolution: {width}x{height}",
                (15, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )

            cv2.imshow("CCTV Serang Timur", frame)

        else:
            # Tunggu sebentar jika frame belum tersedia
            if time.time() - last_frame_time >= RECONNECT_AFTER:
                print("Stream terputus. Mencoba koneksi ulang...")

                cap.release()
                time.sleep(2)
                cap = open_stream()

                if cap is None:
                    print("Koneksi ulang gagal. Mencoba lagi...")
                    time.sleep(3)
                    cap = open_stream()

                    if cap is None:
                        continue

                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                last_frame_time = time.time()

            time.sleep(0.05)

        # Batasi laju tampilan, bukan kecepatan sumber stream
        elapsed = time.time() - loop_start
        delay = max(0, (1 / TARGET_FPS) - elapsed)

        key = cv2.waitKey(max(1, int(delay * 1000))) & 0xFF

        if key == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Program CCTV dihentikan.")
