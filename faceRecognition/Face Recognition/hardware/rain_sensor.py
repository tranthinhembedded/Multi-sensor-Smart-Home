import RPi.GPIO as GPIO
import time

# Cấu hình GPIO
RAIN_SENSOR_PIN = 18
SERVO_PIN = 15     

# Thiết lập chế độ chân GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_SENSOR_PIN, GPIO.IN)  
GPIO.setup(SERVO_PIN, GPIO.OUT)       
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)  

# Hàm điều chỉnh góc Servo
def set_servo_angle(angle):
    duty = 2 + (angle / 18)  
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)  # Dừng tín hiệu

try:
    while True:
        rain_detected = GPIO.input(RAIN_SENSOR_PIN)  # Đọc cảm biến mưa

        if rain_detected == 0:  
            print("Trời đang mưa !!!")
            set_servo_angle(0)  
        else:
            print("☀Trời khô ráo !!!")
            set_servo_angle(90)  

        time.sleep(1) 

except KeyboardInterrupt:
    print("\nDừng chương trình, giải phóng GPIO...")
    set_servo_angle(0)
    servo.stop()
    GPIO.cleanup()  