import cv2
import pytesseract
import requests
import time
import re

# 🔗 Flask server
API_URL = "http://127.0.0.1:5000/update"

# 📍 Camera location
LOCATION = "TINDIVANAM"
LAT = 12.229385
LON = 79.651276

# 🎯 Target vehicle
TARGET_PLATES = ["HR99GX0777", "HR98AA0000"]

# Load cascade
plate_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
)

cap = cv2.VideoCapture(0)

last_sent = {}
COOLDOWN = 10
frame_count = 0
PROCESS_EVERY = 3


# 🔹 Clean OCR text
def clean_text(text):
    return re.sub(r'[^A-Z0-9]', '', text.upper())


# 🔹 Fix common OCR mistakes
def fix_ocr_errors(text):
    replacements = {
        'O': '0', 'Q': '0', 'D': '0',
        'I': '1', 'L': '1',
        'Z': '2',
        'S': '5',
        'B': '8'
    }
    return ''.join([replacements.get(c, c) for c in text])


# 🔹 Check if matches target
def is_target(text):
    for plate in TARGET_PLATES:
        if plate in text or text in plate:
            return plate
    return None


print("🚀 Camera started. Press ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # 🔥 Resize for speed
    frame = cv2.resize(frame, (640, 480))

    if frame_count % PROCESS_EVERY != 0:
        cv2.imshow("Detection", frame)
        if cv2.waitKey(1) == 27:
            break
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    plates = plate_cascade.detectMultiScale(gray, 1.2, 5)

    for (x, y, w, h) in plates:
        # 🔥 tighter crop
        plate = gray[y+5:y+h-5, x+5:x+w-5]

        # 🔥 preprocess
        plate = cv2.GaussianBlur(plate, (5,5), 0)
        _, plate = cv2.threshold(plate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        text = pytesseract.image_to_string(
            plate,
            config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )

        text = clean_text(text)
        text = fix_ocr_errors(text)

        if len(text) >= 6:
            cv2.putText(frame, text, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            print("Detected:", text)

            # 🎯 ONLY YOUR VEHICLE
            matched_plate = is_target(text)

            if matched_plate:
                print("✅ TARGET DETECTED:", matched_plate)

                now = time.time()

                if text not in last_sent or (now - last_sent[text]) > COOLDOWN:
                    try:
                        res = requests.post(API_URL, json={
                            "bus_no": matched_plate,
                            "location": LOCATION,
                            "lat": LAT,
                            "lon": LON,
                            "route": "Camera Route"
                        })

                        print("📡 Sent to server:", res.status_code)

                        last_sent[text] = now

                    except Exception as e:
                        print("❌ Error:", e)

    cv2.imshow("Detection", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows() 