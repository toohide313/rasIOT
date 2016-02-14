# -*- coding: utf-8 -*-
import sys
import os.path

def initGPIO(gpionum):
	path = "/sys/class/gpio/gpio" + gpionum
	if ( os.path.isdir(path) == 0 ):
		print "gpio %s not setup" % gpionum
		f = open('/sys/class/gpio/export', 'w')
		f.write(str(gpionum))
		f.close()
	else:
		return
	fpath = "/sys/class/gpio/gpio" + gpionum + "/direction"
	if ( os.path.isfile(fpath) == 1 ):
		f = open(fpath, 'w')
		f.write("out")
		f.close()

def getGPIO(gpionum):
	initGPIO(gpionum)
	vpath = "/sys/class/gpio/gpio" + gpionum + "/value"
	f = open(vpath , 'r')
	status = f.readline()	
	status = status.rstrip()
#	print "get %s" % gpionum
#	print "val %s" % status
	return status

def setGPIO(gpionum,val):
	initGPIO(gpionum)
	vpath = "/sys/class/gpio/gpio" + gpionum + "/value"
	f = open(vpath, 'w')
	f.write(val)
	f.close()
#	print "set %s" % gpionum
#	print "val %s" % val

if __name__ == "__main__":
    param = sys.argv
    if( len(param) == 2 ):
	getGPIO(param[1])
    if( len(param) == 3 ):
	setGPIO(param[1],param[2])

