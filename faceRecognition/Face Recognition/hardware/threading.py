import threading
import RPi.GPIO as GPIO
import time

# Function for the rain sensor thread
def rain_sensor_thread(stop_event):
    RAIN_SENSOR_PIN = 18
    SERVO_PIN = 15
    GPIO.setup(RAIN_SENSOR_PIN, GPIO.IN)  # Set rain sensor pin as input
    GPIO.setup(SERVO_PIN, GPIO.OUT)       # Set servo pin as output
    servo = GPIO.PWM(SERVO_PIN, 50)       # Initialize PWM for servo at 50Hz
    servo.start(0)                        # Start servo with 0% duty cycle

    def set_servo_angle(angle):
        duty = 2 + (angle / 18)           # Calculate duty cycle for the given angle
        GPIO.output(SERVO_PIN, True)      # Activate servo
        servo.ChangeDutyCycle(duty)       # Set the duty cycle
        time.sleep(0.5)                   # Wait for servo to move
        GPIO.output(SERVO_PIN, False)     # Deactivate servo
        servo.ChangeDutyCycle(0)          # Reset duty cycle to 0

    while not stop_event.is_set():        # Loop until stop event is triggered
        rain_detected = GPIO.input(RAIN_SENSOR_PIN)
        if rain_detected == 0:
            print("It's raining !!!")     # Display message when rain is detected
            set_servo_angle(0)            # Set servo to 0 degrees
        else:
            print("☀ It's dry !!!")       # Display message when no rain is detected
            set_servo_angle(90)           # Set servo to 90 degrees
        time.sleep(1)                     # Wait 1 second before next check

    # Clean up servo before exiting
    set_servo_angle(0)                    # Reset servo to 0 degrees
    servo.stop()                          # Stop PWM for servo

# Function for the gas sensor thread
def gas_sensor_thread(stop_event):
    INPUT_PIN = 17
    BUZZER = 2
    LED1 = 3
    LED2 = 4
    GPIO.setup(INPUT_PIN, GPIO.IN)        # Set gas sensor pin as input
    GPIO.setup(BUZZER, GPIO.OUT)          # Set buzzer pin as output
    GPIO.setup(LED1, GPIO.OUT)            # Set LED1 pin as output
    GPIO.setup(LED2, GPIO.OUT)            # Set LED2 pin as output
    GPIO.output(LED1, GPIO.HIGH)          # Turn on LED1 initially
    GPIO.output(LED2, GPIO.HIGH)          # Turn on LED2 initially

    while not stop_event.is_set():        # Loop until stop event is triggered
        if GPIO.input(INPUT_PIN):
            print("I'm reading TRUE on GPIO 17")  # Display message for TRUE reading
            GPIO.output(BUZZER, GPIO.LOW)     # Turn off buzzer
            GPIO.output(LED1, GPIO.HIGH)      # Turn on LED1
            GPIO.output(LED2, GPIO.HIGH)      # Turn on LED2
        else:
            print("I'm reading FALSE on GPIO 17") # Display message for FALSE reading
            GPIO.output(BUZZER, GPIO.HIGH)    # Turn on buzzer
            GPIO.output(LED1, GPIO.LOW)       # Turn off LED1
            GPIO.output(LED2, GPIO.LOW)       # Turn off LED2
        time.sleep(1)                         # Wait 1 second before next check

# Main part of the program
if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)                    # Set GPIO mode to BCM numbering

    # Create a stop event for the threads
    stop_event = threading.Event()

    # Create and start the threads
    rain_thread = threading.Thread(target=rain_sensor_thread, args=(stop_event,))
    gas_thread = threading.Thread(target=gas_sensor_thread, args=(stop_event,))
    rain_thread.start()                       # Start rain sensor thread
    gas_thread.start()                        # Start gas sensor thread

    try:
        # Keep the main thread running to catch interrupts
        while True:
            time.sleep(0.1)                   # Sleep briefly to reduce CPU usage
    except KeyboardInterrupt:
        print("\nStopping threads...")        # Display message when stopping
        stop_event.set()                      # Signal threads to stop
        rain_thread.join()                    # Wait for rain sensor thread to finish
        gas_thread.join()                     # Wait for gas sensor thread to finish
        print("Cleaning up GPIO...")          # Display message for GPIO cleanup
        GPIO.cleanup()                        # Clean up all GPIO pins