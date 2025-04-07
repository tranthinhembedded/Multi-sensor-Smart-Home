from flask import Flask, Response, render_template
import cv2
import numpy as np
import time
import pickle
import face_recognition
import RPi.GPIO as GPIO
import threading

app = Flask(__name__)

# Thiết lập GPIO cho servo
GPIO.setmode(GPIO.BCM)
servo_pin = 14
GPIO.setup(servo_pin, GPIO.OUT)
pwm = GPIO.PWM(servo_pin, 50)
pwm.start(0)

# Load dữ liệu khuôn mặt đã train
print("[INFO] loading encodings...")
encoding_file = "/home/pi/Desktop/faceRecognition/Face Recognition/encodings.pickle"
with open(encoding_file, "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

# Biến kiểm soát chế độ nhận diện và trạng thái cửa
face_id_active = False  # Flag để bật/tắt nhận diện
cv_scaler = 4  # Hệ số thu nhỏ để tăng hiệu suất
door_opened = False  # Flag để theo dõi trạng thái cửa

# Hàm điều khiển servo
def set_servo_angle(angle):
    duty = angle / 18 + 2
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

# Khởi tạo servo ở góc 0 độ (cửa đóng)
set_servo_angle(0)

# Hàm đóng cửa sau 10 giây
def close_door_after_delay():
    global door_opened
    time.sleep(5)  # Chờ 10 giây
    set_servo_angle(0)  # Đóng cửa
    door_opened = False
    print("Cửa đã đóng sau 5 giây.")

# Hàm xử lý frame với nhận diện khuôn mặt
def process_frame(frame):
    global face_id_active, door_opened
    if not face_id_active:
        return frame  # Nếu không bật  ID, trả về frame gốc

    # Thu nhỏ frame để xử lý nhanh hơn
    resized_frame = cv2.resize(frame, (0, 0), fx=(1/cv_scaler), fy=(1/cv_scaler))
    rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    
    # Tìm vị trí và mã hóa khuôn mặt
    face_locations = face_recognition.face_locations(rgb_resized_frame)
    face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations, model='large')
    
    face_names = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
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
        cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 3)
        cv2.rectangle(frame, (left - 3, top - 35), (right + 3, top), (244, 42, 3), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, top - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
    
    # Điều khiển servo dựa trên kết quả nhận diện
    if "Unknown" not in face_names and face_names and not door_opened:
        set_servo_angle(90)  # Mở cửa
        door_opened = True
        face_id_active = False  # Ngừng nhận diện
        threading.Thread(target=close_door_after_delay).start()  # Đóng cửa sau 10 giây
    elif not face_names or "Unknown" in face_names:
        set_servo_angle(0)  # Đóng cửa nếu không nhận diện được hoặc là "Unknown"

    return frame

# Hàm stream video
def generate_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không thể mở camera")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            processed_frame = process_frame(frame)
            _, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

# Các route
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route('/start_face_id')
def start_face_id():
    global face_id_active
    face_id_active = True
    return 'Bắt đầu FACE ID'
@app.route('/open_door')
def open_door():
    set_servo_angle(90)
    return 'Door opened'
@app.route('/close_door')
def close_door():
    set_servo_angle(0)
    return 'Door closed'

if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False, host='0.0.0.0')
        
    finally:
        pwm.stop()
        GPIO.cleanup()
