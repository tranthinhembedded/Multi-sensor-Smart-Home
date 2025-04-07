import lgpio
chip = lgpio.gpiochip_open(0)
lgpio.gpio_free(chip, 14)
lgpio.gpiochip_close(chip)
print("GPIO14 freed.")