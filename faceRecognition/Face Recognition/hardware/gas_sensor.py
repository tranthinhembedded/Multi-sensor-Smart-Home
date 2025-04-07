import RPi.GPIO as GPIO
from time import sleep

# Set GPIO numbering mode to BCM
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
INPUT_PIN = 17  # Input pin for reading signal
BUZZER = 2      # Buzzer on GPIO2
LED1 = 3        # First LED on GPIO3
LED2 = 4        # Second LED on GPIO4

# Setup GPIO pins
GPIO.setup(INPUT_PIN, GPIO.IN)   # Set GPIO17 as input
GPIO.setup(BUZZER, GPIO.OUT)     # Set GPIO2 as output for buzzer
GPIO.setup(LED1, GPIO.OUT)       # Set GPIO3 as output for LED
GPIO.setup(LED2, GPIO.OUT)       # Set GPIO4 as output for LED

# Turn on all outputs initially (LEDs on)
GPIO.output(LED1, GPIO.HIGH)
GPIO.output(LED2, GPIO.HIGH)

try:
    while True:
        if GPIO.input(INPUT_PIN):  # If GPIO17 reads TRUE
            print("I'm reading TRUE on GPIO 17")
            GPIO.output(BUZZER, GPIO.LOW)  # Turn off buzzer
            GPIO.output(LED1, GPIO.HIGH)   # Keep LED on GPIO3 on
            GPIO.output(LED2, GPIO.HIGH)   # Keep LED on GPIO4 on
        else:  # If GPIO17 reads FALSE
            print("I'm reading FALSE on GPIO 17")
            GPIO.output(BUZZER, GPIO.HIGH)  # Turn on buzzer
            GPIO.output(LED1, GPIO.LOW)     # Turn off LED on GPIO3
            GPIO.output(LED2, GPIO.LOW)     # Turn off LED on GPIO4
        sleep(1)  # Wait for 1 second between readings

except KeyboardInterrupt:
    print("\nProgram stopped by user")

finally:
    print("Cleaning up GPIO settings...")
    GPIO.cleanup()  # Reset all GPIO pins to default state