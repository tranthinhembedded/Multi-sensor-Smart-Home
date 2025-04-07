import RPi.GPIO as GPIO  # Import the GPIO library for Raspberry Pi
import time             # Import the time library for delays

# Set the GPIO numbering mode to BCM
GPIO.setmode(GPIO.BCM)

# Define the GPIO pins
LED1 = 3  # GPIO3
LED2 = 4  # GPIO4

# Set up the pins as outputs
GPIO.setup(LED1, GPIO.OUT)
GPIO.setup(LED2, GPIO.OUT)

try:
    while True:
        # Turn on all LEDs
        GPIO.output(LED1, GPIO.HIGH)
        GPIO.output(LED2, GPIO.HIGH)
        print("LED ON")         # Print status to console
        time.sleep(1)           # Wait for 1 second
        
        # Turn off all LEDs
        GPIO.output(LED1, GPIO.LOW)
        GPIO.output(LED2, GPIO.LOW)
        print("LED OFF")        # Print status to console
        time.sleep(1)           # Wait for 1 second

except KeyboardInterrupt:
    # Handle Ctrl+C to exit the program
    print("\nProgram stopped")  # Notify when program stops
    
finally:
    # Clean up GPIO settings
    GPIO.cleanup()              # Reset GPIO pins to default state