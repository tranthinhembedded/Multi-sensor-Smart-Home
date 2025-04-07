from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
servo_pin = 14
GPIO.setup(servo_pin, GPIO.OUT)
pwm = GPIO.PWM(servo_pin, 50)
pwm.start(0)


# Function to set the servo angle
def set_angle(angle):
    duty = angle / 18 + 2
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(duty)
    sleep(1)
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

# Main program loop
try:
    while True:
        angle = int(input("Enter angle (0 to 180): "))  # User input for angle
        set_angle(angle)  # Set servo to entered angle

except KeyboardInterrupt:
    print("Program stopped by user")
    pwm.stop()
    GPIO.cleanup()
    
    