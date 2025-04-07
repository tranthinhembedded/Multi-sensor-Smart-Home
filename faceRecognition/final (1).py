import threading
import time
import RPi.GPIO as GPIO
import cv2
import numpy as np
import pickle
import face_recognition
from flask import Flask, Response, render_template
import webbrowser

# CẤU HÌNH GPIO
GPIO.setmode(GPIO.BCM)

# --- Servo cho điều khiển cửa (chân 14) ---
DOOR_SERVO_PIN = 14
GPIO.setup(DOOR_SERVO_PIN, GPIO.OUT)
door_servo_lock = threading.Lock()
door_servo = GPIO.PWM(DOOR_SERVO_PIN, 50)
door_servo.start(0)

def set_door_servo_angle(angle):
    """Điều khiển servo cửa trên chân 14"""
    with door_servo_lock:
        duty = 2 + (angle / 18)
        GPIO.output(DOOR_SERVO_PIN, True)
        door_servo.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(DOOR_SERVO_PIN, False)
        door_servo.ChangeDutyCycle(0)

# --- Servo cho cảm biến mưa (chân 15) ---
RAIN_SERVO_PIN = 15
GPIO.setup(RAIN_SERVO_PIN, GPIO.OUT)
rain_servo_lock = threading.Lock()
rain_servo = GPIO.PWM(RAIN_SERVO_PIN, 50)
rain_servo.start(0)

def set_rain_servo_angle(angle):
    """Điều khiển servo cho cảm biến mưa trên chân 15"""
    with rain_servo_lock:
        duty = 2 + (angle / 18)
        GPIO.output(RAIN_SERVO_PIN, True)
        rain_servo.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(RAIN_SERVO_PIN, False)
        rain_servo.ChangeDutyCycle(0)

# ===================== Hàm Face Recognition =====================
def face_recognition_thread(stop_event):
    """
    Hàm chạy Flask web server tích hợp nhận diện khuôn mặt.
    Các route và xử lý nhận diện được định nghĩa bên trong.
    Khi nhận diện thành công, servo cửa (chân 14) sẽ được điều khiển.
    """
    app = Flask(__name__)

    # Load dữ liệu khuôn mặt đã train
    encoding_file = "/home/pi/Desktop/faceRecognition/Face Recognition/encodings.pickle"
    with open(encoding_file, "rb") as f:
        data = pickle.loads(f.read())
    known_face_encodings = data["encodings"]
    known_face_names = data["names"]

    # Các biến điều khiển nội bộ
    face_id_active = False   # Cờ kích hoạt nhận diện khuôn mặt
    cv_scaler = 4            # Hệ số thu nhỏ để tăng hiệu suất xử lý
    door_opened = False       # Trạng thái cửa (đã mở hay chưa)

    def process_frame(frame):
        nonlocal face_id_active, door_opened
        if not face_id_active:
            return frame

        # Thu nhỏ frame để xử lý nhanh hơn
        resized_frame = cv2.resize(frame, (0, 0), fx=1/cv_scaler, fy=1/cv_scaler)
        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        # Nhận diện vị trí và mã hóa khuôn mặt
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, model='large')

        face_names = []
        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, encoding)
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_face_encodings, encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            face_names.append(name)

        # Vẽ hộp và tên lên frame
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= cv_scaler
            right *= cv_scaler
            bottom *= cv_scaler
            left *= cv_scaler
            cv2.rectangle(frame, (left, top), (right, bottom), (244,42,3), 3)
            cv2.rectangle(frame, (left-3, top-35), (right+3, top), (244,42,3), cv2.FILLED)
            cv2.putText(frame, name, (left+6, top-6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,255,255), 1)

        # Nếu nhận diện được khuôn mặt hợp lệ, mở cửa
        if "Unknown" not in face_names and face_names and not door_opened:
            set_door_servo_angle(90)  # Mở cửa
            door_opened = True
            face_id_active = False  # Dừng nhận diện sau khi mở cửa
            threading.Thread(target=close_door_after_delay).start()
        # Nếu không nhận diện được hoặc nhận diện "Unknown", đảm bảo cửa đóng
        elif not face_names or "Unknown" in face_names:
            set_door_servo_angle(0)  # Đóng cửa

        return frame

    def close_door_after_delay():
        nonlocal door_opened
        time.sleep(5)  # Đợi 5 giây trước khi đóng cửa
        set_door_servo_angle(0)
        door_opened = False
        print("Cửa đã đóng sau 5 giây.")

    def generate_frames():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Không thể mở camera")
            return
        while not stop_event.is_set():
            success, frame = cap.read()
            if not success:
                break
            processed_frame = process_frame(frame)
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        cap.release()

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    @app.route('/open_door')
    def open_door():
        set_door_servo_angle(90)
        return 'Door opened'
    @app.route('/close_door')
    def close_door():
        set_door_servo_angle(0)
        return 'Door closed'
    @app.route('/start_face_id')
    def start_face_id():
        nonlocal face_id_active
        face_id_active = True
        return "Bắt đầu FACE ID"

    # Tự động mở trình duyệt sau khi server khởi chạy
    threading.Timer(1.0, lambda: webbrowser.open_new("http://127.0.0.1:5000/")).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ===================== Hàm Gas Sensor =====================
def gas_sensor_thread(stop_event, gas_ok_event):
    INPUT_PIN = 17
    BUZZER = 2
    LED1 = 3
    LED2 = 4
    GPIO.setup(INPUT_PIN, GPIO.IN)
    GPIO.setup(BUZZER, GPIO.OUT)
    GPIO.setup(LED1, GPIO.OUT)
    GPIO.setup(LED2, GPIO.OUT)
    GPIO.output(LED1, GPIO.HIGH)
    GPIO.output(LED2, GPIO.HIGH)
    GPIO.output(BUZZER, GPIO.LOW)

    while not stop_event.is_set():
        sensor_value = GPIO.input(INPUT_PIN)
        if not sensor_value:
            if gas_ok_event.is_set():
                print("Gas sensor detected FALSE signal - Emergency!")
                GPIO.output(BUZZER, GPIO.HIGH)
                GPIO.output(LED1, GPIO.LOW)
                GPIO.output(LED2, GPIO.LOW)
                set_door_servo_angle(90)  
                gas_ok_event.clear()
        else:
            if not gas_ok_event.is_set():
                print("Gas sensor back to TRUE. Resuming normal operations.")
                GPIO.output(BUZZER, GPIO.LOW)
                GPIO.output(LED1, GPIO.HIGH)
                GPIO.output(LED2, GPIO.HIGH)
                set_door_servo_angle(0)  # Đóng cửa
                gas_ok_event.set()
            else:
                print("Gas sensor reading TRUE")
        time.sleep(1)

# ===================== Hàm Rain Sensor =====================
def rain_sensor_thread(stop_event, gas_ok_event):
    RAIN_SENSOR_PIN = 18
    GPIO.setup(RAIN_SENSOR_PIN, GPIO.IN)
    while not stop_event.is_set():
        # Nếu tín hiệu khí ga không an toàn, thread chờ
        gas_ok_event.wait()
        rain_detected = GPIO.input(RAIN_SENSOR_PIN)
        if rain_detected == 0:
            print("It's raining !!!")
            set_rain_servo_angle(0)  # Sử dụng servo chân 15 để đóng cửa khi mưa
        else:
            print("It's dry !!!")
            set_rain_servo_angle(90)  # Sử dụng servo chân 15 để mở cửa khi khô
        time.sleep(1)

# ===================== MAIN PROGRAM =====================
if __name__ == "__main__":
    stop_event = threading.Event()
    gas_ok_event = threading.Event()
    gas_ok_event.set()  # Khởi tạo trạng thái an toàn

    # Tạo các luồng cho Face Recognition, Gas Sensor và Rain Sensor
    face_thread = threading.Thread(target=face_recognition_thread, args=(stop_event,))
    gas_thread = threading.Thread(target=gas_sensor_thread, args=(stop_event, gas_ok_event))
    rain_thread = threading.Thread(target=rain_sensor_thread, args=(stop_event, gas_ok_event))

    # Khởi chạy các luồng
    face_thread.start()
    gas_thread.start()
    rain_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()

    face_thread.join()
    gas_thread.join()
    rain_thread.join()

    # Dừng PWM và dọn dẹp GPIO khi kết thúc
    door_servo.stop()
    rain_servo.stop()
    GPIO.cleanup()
