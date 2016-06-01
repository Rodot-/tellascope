'''
Define a class for the LX200 telescope
'''
import time

class LX200:

	def __init__(self, ser, sleep = 0.1):
		'''We could do the initialization 
		of the serial object inside this too, though
		it might break generality.'''
		self.ser = ser
		self.sleep = sleep	
	
	def send(self, command):

		self.ser.write(command.join(':#'))

	def recv(self, sleep = None):

		if sleep is not None: time.sleep(sleep)
		return self.ser.read_all()

	def get(self, command):

		self.send(command)
		return self.recv(self.sleep)

	def slew(self, direction):
		'''direction is either n, e, s, w'''

		command = 'M'+direction
		self.send(command)
		return None
	
	def halt(self, direction = ''):
		'''direction is either n, w, s, w or empty string to stop all movement'''
		command = 'Q' + direction
		self.send(command)
		return None
	
	def getLocalTime(self):

		return self.get("Ga")

	def getAltitude(self):
	
		return self.get("GA")
	
	def getBrowseBrighterMagnitudeLimit(self):

		return self.get("Gb")

	def getCurrentData(self):
		
		return self.get("GC")

	def getCalendarFormat(self):

		return self.get("Gc")

def test():

	from serial import Serial
	ser = Serial('/dev/ttyUSB0', timeout = 0.1)
	scope = LX200(ser)
	print scope.getAltitude()
	scope.slew('e')
	time.sleep(1)
	scope.halt('e')
	print scope.getAltitude()

	pass
 
