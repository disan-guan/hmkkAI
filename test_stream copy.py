
import cv2

STREAM_URL = "https://stream.serangkota.go.id/LiveApp/streams/serangtimur.m3u8"

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Gagal membuka stream.")
    print("Periksa URL, koneksi, dan dukungan format stream.")
    raise SystemExit(1)

print("Stream berhasil dibuka. Tekan Q untuk keluar.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame tidak diterima.")
        break

    cv2.imshow("Public CCTV Stream Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
