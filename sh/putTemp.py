#coding: utf-8
import os
import smbus
import time
from socket import gethostname
from ConfigParser import SafeConfigParser

bus_number  = 1
i2c_address = 0x76

bus = smbus.SMBus(bus_number)

digT = []
digP = []
digH = []

t_fine = 0.0

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
#       print "get %s" % gpionum
#       print "val %s" % status
        return status

def setGPIO(gpionum,val):
        initGPIO(gpionum)
        vpath = "/sys/class/gpio/gpio" + gpionum + "/value"
        f = open(vpath, 'w')
        f.write(val)
        f.close()
#       print "set %s" % gpionum
#       print "val %s" % val

def writeReg(reg_address, data):
	bus.write_byte_data(i2c_address,reg_address,data)

def get_calib_param():
	calib = []
	
	for i in range (0x88,0x88+24):
		calib.append(bus.read_byte_data(i2c_address,i))
	calib.append(bus.read_byte_data(i2c_address,0xA1))
	for i in range (0xE1,0xE1+7):
		calib.append(bus.read_byte_data(i2c_address,i))

	digT.append((calib[1] << 8) | calib[0])
	digT.append((calib[3] << 8) | calib[2])
	digT.append((calib[5] << 8) | calib[4])
	digP.append((calib[7] << 8) | calib[6])
	digP.append((calib[9] << 8) | calib[8])
	digP.append((calib[11]<< 8) | calib[10])
	digP.append((calib[13]<< 8) | calib[12])
	digP.append((calib[15]<< 8) | calib[14])
	digP.append((calib[17]<< 8) | calib[16])
	digP.append((calib[19]<< 8) | calib[18])
	digP.append((calib[21]<< 8) | calib[20])
	digP.append((calib[23]<< 8) | calib[22])
	digH.append( calib[24] )
	digH.append((calib[26]<< 8) | calib[25])
	digH.append( calib[27] )
	digH.append((calib[28]<< 4) | (0x0F & calib[29]))
	digH.append((calib[30]<< 4) | ((calib[29] >> 4) & 0x0F))
	digH.append( calib[31] )
	
	for i in range(1,2):
		if digT[i] & 0x8000:
			digT[i] = (-digT[i] ^ 0xFFFF) + 1

	for i in range(1,8):
		if digP[i] & 0x8000:
			digP[i] = (-digP[i] ^ 0xFFFF) + 1

	for i in range(0,6):
		if digH[i] & 0x8000:
			digH[i] = (-digH[i] ^ 0xFFFF) + 1  

def readGPIO():
	filename = '/home/pi/rasIOT/conf/'+gethostname()+'.conf'

	if not os.path.exists(filename):
        	raise IOError(filename)

	parser = SafeConfigParser()
	parser.read(filename)
	str=""
	words = parser.get('gpio','gpio')
	for word in words.split():
		str = str + "&gpio"+word+"="+getGPIO(word)
	return str

def readData():
	data = []
	for i in range (0xF7, 0xF7+8):
		data.append(bus.read_byte_data(i2c_address,i))
	pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
	temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
	hum_raw  = (data[6] << 8)  |  data[7]
	
	hw_cpu = compensate_CPU()
	hw_clock = compensate_CLOCK()
	temp = compensate_T(temp_raw)
	pressure = compensate_P(pres_raw)
	humid = compensate_H(hum_raw)

	return "hw_temp="+hw_cpu+"&hw_clock="+hw_clock+"&temp="+temp+"&humid="+humid+"&pressure="+pressure

def compensate_CPU():
	f = open("/sys/class/thermal/thermal_zone0/temp","r")
	for t in f:
		cpu = t.rstrip()
	f.close()
	return cpu

def compensate_CLOCK():
	f = open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r")
	for t in f:
	#	print "CPU CLOCK:"+t[:2]+"."+t[2:] ,
		clock = t.rstrip()
	f.close()
	return clock

def compensate_P(adc_P):
	global  t_fine
	pressure = 0.0
	
	v1 = (t_fine / 2.0) - 64000.0
	v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * digP[5]
	v2 = v2 + ((v1 * digP[4]) * 2.0)
	v2 = (v2 / 4.0) + (digP[3] * 65536.0)
	v1 = (((digP[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)) / 8)  + ((digP[1] * v1) / 2.0)) / 262144
	v1 = ((32768 + v1) * digP[0]) / 32768
	
	if v1 == 0:
		return 0
	pressure = ((1048576 - adc_P) - (v2 / 4096)) * 3125
	if pressure < 0x80000000:
		pressure = (pressure * 2.0) / v1
	else:
		pressure = (pressure / v1) * 2
	v1 = (digP[8] * (((pressure / 8.0) * (pressure / 8.0)) / 8192.0)) / 4096
	v2 = ((pressure / 4.0) * digP[7]) / 8192.0
	pressure = pressure + ((v1 + v2 + digP[6]) / 16.0)  

	# print "pressure : %7.2f hPa" % (pressure/100)
	return "%d" % ( pressure / 100 )

def compensate_T(adc_T):
	global t_fine
	v1 = (adc_T / 16384.0 - digT[0] / 1024.0) * digT[1]
	v2 = (adc_T / 131072.0 - digT[0] / 8192.0) * (adc_T / 131072.0 - digT[0] / 8192.0) * digT[2]
	t_fine = v1 + v2
	temperature = t_fine / 5120.0
	# print "temp : %-6.2f ℃" % (temperature) 
	return str( "%2.2f" % temperature )

def compensate_H(adc_H):
	global t_fine
	var_h = t_fine - 76800.0
	if var_h != 0:
		var_h = (adc_H - (digH[3] * 64.0 + digH[4]/16384.0 * var_h)) * (digH[1] / 65536.0 * (1.0 + digH[5] / 67108864.0 * var_h * (1.0 + digH[2] / 67108864.0 * var_h)))
	else:
		return 0
	var_h = var_h * (1.0 - digH[0] * var_h / 524288.0)
	if var_h > 100.0:
		var_h = 100.0
	elif var_h < 0.0:
		var_h = 0.0
	# print "hum : %6.2f ％" % (var_h)
	return str( "%2.2f" % var_h )

def setup():
	osrs_t = 1			#Temperature oversampling x 1
	osrs_p = 1			#Pressure oversampling x 1
	osrs_h = 1			#Humidity oversampling x 1
	mode   = 3			#Normal mode
	t_sb   = 5			#Tstandby 1000ms
	filter = 0			#Filter off
	spi3w_en = 0			#3-wire SPI Disable

	ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
	config_reg    = (t_sb << 5) | (filter << 2) | spi3w_en
	ctrl_hum_reg  = osrs_h

	writeReg(0xF2,ctrl_hum_reg)
	writeReg(0xF4,ctrl_meas_reg)
	writeReg(0xF5,config_reg)


setup()
get_calib_param()


if __name__ == '__main__':
	try:
		para = readData() + readGPIO()

		import urllib2

		password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_mgr.add_password(None, 'http://dons.sakura.ne.jp', 'oikawa', '6404')

		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		urllib2.install_opener(opener)
		url_str = 'http://dons.sakura.ne.jp/sv/setTemp.cgi'
		param_str = '?node='+gethostname()+"&"+para
		f = urllib2.urlopen( url_str + param_str )

#		print "get:"+url_str+param_str
		# 取得した内容を出力する
#		print f.read()
		cnt = 0
		for str in f.readlines():
			word = str.split()
			cnt = cnt + 1
#			print " %d " % cnt
			if ( "gpio" in word[0] ) and ( len(word) == 2 ):
				t = word[0][4:]
#				print " %s " % word
#				print " %s " % t
				setGPIO(t,word[1])

	except KeyboardInterrupt:
		pass





