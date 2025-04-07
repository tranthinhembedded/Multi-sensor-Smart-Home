import threading
import RPi.GPIO as GPIO
import time
import runpy

# Luồng cảm biến mưa (rain sensor) – sẽ tạm dừng khi trạng thái khí ga không OK
def rain_sensor_thread(stop_event, gas_ok_event):
    RAIN_SENSOR_PIN = 18
    SERVO_PIN = 15
    GPIO.setup(RAIN_SENSOR_PIN, GPIO.IN)  # Cấu hình chân cảm biến mưa
    GPIO.setup(SERVO_PIN, GPIO.OUT)       # Cấu hình chân servo
    servo = GPIO.PWM(SERVO_PIN, 50)         # Khởi tạo PWM cho servo 50Hz
    servo.start(0)                          # Bắt đầu với 0% duty cycle

    def set_servo_angle(angle):
        duty = 2 + (angle / 18)
        GPIO.output(SERVO_PIN, True)
        servo.ChangeDutyCycle(duty)
        time.sleep(0.5)
        GPIO.output(SERVO_PIN, False)
        servo.ChangeDutyCycle(0)

    while not stop_event.is_set():
        # Nếu trạng thái khí ga không OK, thread sẽ chờ tại đây cho đến khi được báo "resume"
        gas_ok_event.wait()
        
        rain_detected = GPIO.input(RAIN_SENSOR_PIN)
        if rain_detected == 0:
            print("It's raining !!!")
            set_servo_angle(0)
        else:
            print("☀ It's dry !!!")
            set_servo_angle(90)
        time.sleep(1)

    set_servo_angle(0)
    servo.stop()

# Luồng cảm biến khí ga với độ ưu tiên cao nhất
def gas_sensor_thread(stop_event, gas_ok_event):
    INPUT_PIN = 17
    BUZZER = 2
    LED1 = 3
    LED2 = 4
    GPIO.setup(INPUT_PIN, GPIO.IN)      # Cấu hình chân cảm biến khí ga
    GPIO.setup(BUZZER, GPIO.OUT)        # Cấu hình chân buzzer
    GPIO.setup(LED1, GPIO.OUT)          # Cấu hình chân LED1
    GPIO.setup(LED2, GPIO.OUT)          # Cấu hình chân LED2
    GPIO.output(LED1, GPIO.HIGH)        # Bật LED1 ban đầu
    GPIO.output(LED2, GPIO.HIGH)        # Bật LED2 ban đầu
    GPIO.output(BUZZER, GPIO.LOW)

    # Khởi tạo servo riêng dùng trong trường hợp khẩn cấp
    DOOR_SERVO_PIN = 14
    GPIO.setup(DOOR_SERVO_PIN, GPIO.OUT)
    door_servo = GPIO.PWM(DOOR_SERVO_PIN, 50)
    door_servo.start(0)

    def set_door_servo_angle(angle):
        duty = 2 + (angle / 18)
        GPIO.output(DOOR_SERVO_PIN, True)
        door_servo.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(DOOR_SERVO_PIN, False)
        door_servo.ChangeDutyCycle(0)

    while not stop_event.is_set():
        sensor_value = GPIO.input(INPUT_PIN)
        if not sensor_value:  # Nếu tín hiệu FALSE (không an toàn)
            if gas_ok_event.is_set():
                print("Gas sensor detected FALSE signal - Emergency!")
                # Kích hoạt báo động
                GPIO.output(BUZZER, GPIO.HIGH)
                # Tắt LED
                GPIO.output(LED1, GPIO.LOW)
                GPIO.output(LED2, GPIO.LOW)
                # Mở cửa khẩn cấp
                set_door_servo_angle(90)
                # Tạm dừng các luồng khác
                gas_ok_event.clear()
        else:  # Tín hiệu TRUE
            if not gas_ok_event.is_set():
                print("Gas sensor back to TRUE. Resuming normal operations.")
                # Tắt báo động và khôi phục LED
                GPIO.output(BUZZER, GPIO.LOW)
                GPIO.output(LED1, GPIO.HIGH)
                GPIO.output(LED2, GPIO.HIGH)
                # Đóng cửa trở lại (có thể thay đổi theo yêu cầu)
                set_door_servo_angle(0)
                # Cho phép các luồng khác tiếp tục hoạt động
                gas_ok_event.set()
            else:
                print("Gas sensor reading TRUE")
        time.sleep(1)
    door_servo.stop()

# Luồng chạy Flask web server (luôn chạy)
def run_flask_server(stop_event):
    print("Flask web server is running ")
    runpy.run_path("/home/pi/Desktop/faceRecognition/app.py")

# Phần main của chương trình
if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ BCM cho GPIO

    # Tạo sự kiện dừng và sự kiện kiểm tra trạng thái khí ga (True: an toàn, False: emergency)
    stop_event = threading.Event()
    gas_ok_event = threading.Event()
    gas_ok_event.set()  # Khởi tạo ở trạng thái True (an toàn)

    # Tạo các luồng
    rain_thread = threading.Thread(target=rain_sensor_thread, args=(stop_event, gas_ok_event))
    gas_thread = threading.Thread(target=gas_sensor_thread, args=(stop_event, gas_ok_event))
    flask_thread = threading.Thread(target=run_flask_server, args=(stop_event,))

    # Khởi chạy các luồng
    rain_thread.start()
    gas_thread.start()
    flask_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()

    rain_thread.join()
    gas_thread.join()
    flask_thread.join()

    print("Cleaning up GPIO...")
    GPIO.cleanup()

