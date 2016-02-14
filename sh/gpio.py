import RPi.GPIO as GPIO
import time


IO_NO = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(IO_NO, GPIO.IN)
stat = GPIO.input(IO_NO)
print "GPIO" + str (IO_NO) + " " + str ( stat )

GPIO.setup(IO_NO, GPIO.OUT)
if stat:
	GPIO.output(IO_NO, False)
else:
	GPIO.output(IO_NO, True)

GPIO.setup(IO_NO, GPIO.IN)
stat = GPIO.input(IO_NO)
print "GPIO" + str (IO_NO) + " " + str ( stat )

GPIO.cleanup()
