import RPi.GPIO as GPIO
import time

IO_NO = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(IO_NO, GPIO.IN)
stat = GPIO.input(IO_NO)
print "GPIO" + str (IO_NO) + " " + str ( stat )

GPIO.setup(IO_NO, GPIO.OUT)
if stat:
	print "OFF->ON"
	GPIO.output(IO_NO, GPIO.HIGH)
else:
	print "ON->OFF"
	GPIO.output(IO_NO, GPIO.LOW)

GPIO.setup(IO_NO, GPIO.IN)
stat = GPIO.input(IO_NO)
print "GPIO" + str (IO_NO) + " " + str ( stat )

GPIO.cleanup()

