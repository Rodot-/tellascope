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

	pass
 
