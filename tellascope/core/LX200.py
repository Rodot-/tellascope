'''
Python 3.6

Define a class for the LX200 telescope

Right now this is a single case
Will refactor code to have LX200 be a subclass of a telescope metaclass
'''
import time
import serial
from functools import partial
import io

class MockSerial:

	def __init__(self, *args, **kwargs):

		self.args = args
		self.__dict__.update(kwargs)
		self.inbuffer = io.BytesIO()
		self.outbuffer = io.BytesIO()
		self._in_waiting = 0

	def readable(self):

		return True

	def writeable(self):

		return True

	def write(self, *args):

		return self.outbuffer.write(*args)

	def read(self, *args):

		return self.inbuffer.read(*args)

	def process(self):

		data = self.outbuffer.getvalue()
		self.outbuffer.truncate(0)
		self.inbuffer.write(data)

	def reset_input_buffer(self):

		self.inbuffer.truncate(0)

	def reset_output_buffer(self):

		self.outbuffer.truncate(0)

	@property
	def in_waiting(self):

		self.in_waiting = len(buff.getvalue())-buff.tell()
		return self._in_waiting
	

#class SerialInterface(serial.Serial):
class SerialInterface(MockSerial):

	def __init__(self, logfile=None, DELAY=0, *args, **kwargs):

		super().__init__(*args, **kwargs)
		self.clock = time.time()
		self.logfile = logfile
		self.DELAY = DELAY
		self.DELAY_MS = str(int(DELAY*1000)) # for logging and printing

	def set_delay(self, delay):

		self.DELAY = DELAY
		self.DELAY_MS = str(int(DELAY*1000))

	def set_logfile(self, logfile):

		self.logfile = logfile

	def log(self, *text):

		if self.logfile is not None:
			print(*text, file=self.logfile)

	def wait(self):

		elapsed = time.time() - self.clock
		if elapsed < self.DELAY:
			time.sleep(self.DELAY - elapsed) # will switch to asyncio sleep later
		self.clock = time.time()

	def send_str(self, command_string):

		command = command_string.join(':#').encode('ascii')
		self.send(command)

	def send(self, command):

		self.reset_input_buffer() # reset the buffers, will discard old commands and data
		self.reset_output_buffer()

		self.log('Sent:',command, '{')
		n_bytes = self.write(command)
		self.log(' ',n_bytes,'bytes\n}')
		self.clock = time.time() # update the clock to the last send time
		# NOTE: the clock should really start when then '#' terminating the command is recived

	def recv(self, n_bytes=None):
		'''will impliment functionality with n_bytes later to guarantee correct output'''
		self.wait()
		char = ''
		buffer = bytearray()

		self.log("Reading Bytes {")
		if not self.in_waiting:
			self.log("  No data\n}")
			return ''

		while self.port.in_waiting > 0: # while there are bytes in the input buffer to be read

			char = self.read(1)

			if char == 0x15:
				self.log(' ',
					'ASCII NAK (0x15): Telescope control chain busy {\n ',
				  'Waiting for a full delay cycle.',
					'({} ms)\n  }'.format(self.DELAY_MS))
				time.sleep(self.DELAY)

			else:
				buffer.extend(char)

		self.log('  Read:{} {\n    {} bytes\n  }\n}'\
			.format(buffer.hex(), len(buffer)))

		return buffer # this is a bytearray, the telescope object will have to convert it to string

class ObjectInterface:

	def __init__(self, port, logfile=None):

		self.port = port
		self.logfile = logfile

		assert self.port.readable(), "Port unreadable"
		assert self.port.writeable(), "Port is read only"

	def log(self, *text):

		if self.logfile is not None:
			print(*text, file=self.logfile)

	def recv(self, n_bytes=None, callback=None):
		'''abstraction from the port.recv to get ascii response'''
		buffer = self.port.recv(n_bytes)
		message = buffer.decode('ascii')
		if callback is not None:
			callback(message)
		return len(buffer)

	def view_send_recv(self, command_function, *args, **kwargs):
		'''view the output of a command's input for testing'''
		command_function(*args, **kwargs) # this already should send the information to the serial port
		n_bytes = self.recv(callback=print) # set the callback to print to the screen
		if not n_bytes:
			print("(empty string)")

		return n_bytes

	def getter(self, arg, key):
		'''this is temporary, what I really should do is set 
		callbacks that set class attributes	then return those attributes'''
		command = 'G'+arg

		def attribute_callback(msg): # in reality, this will be defined individually for each property
			self.__dict__[key] = msg # this is just the raw data, needs to be processed in the real implimentation

		self.port.send_str(command)
		n_bytes = self.recv(callback=attribute_callback)
		return n_bytes

def _send(command_function):
	'''wrapper for interface container functions for convienience'''
	def _wrapper(self, *args, **kwargs):

		command = command_function(self, *args, **kwargs)\
			.join(':#')\
			.encode('ascii')
		self.port.send(command)

	return _wrapper


class Target(ObjectInterface):

	def __init__(self, port, logfile=None):

		super().__init__(port, logfile)

		self._dec = None
		self._ra = None

	@property
	def declination(self):

		self.getter('d','_dec')
		return self._dec

	@property
	def right_ascension(self):

		self.getter('r','_ra')
		return self._ra	

class ObjectLibrary(ObjectInterface):
	'''Telescope object library'''

	def __init__(self, port, logfile=None):

		super().__init__(port, logfile)

		self.deepsky_catalogs = { # maybe this should be set by implimentation?
			'NGC':'0',
			'IC':'1',
			'UGC':'2',
			'Caldwell':'3',
			'Arp':'4',
			'Abell':'5'
		}

		self.star_catalogs = {
			'STAR':'0',
			'SAO':'1',
			'GCVS':'2',
			'Hipparcos':'3',
			'HR':'4',
			'HD':'5'
		}

	def resolve_catalog_availability(self, available_key, unavailable_key):

		def callback(msg):

			reply = {
				available_key:"Catalog Available",
				unavailable_key:"Catalog Unavailable"
			}[msg]
			self.log(reply)
		
		return callback

	@_send
	def set_previous_target(self):
		'''set current target to the previous target'''

		return 'LB'

	@_send
	def set_target_deepsky(self, number):
		'''set the current target to that defined by 
		the deep sky catalog object number
		The number must be a string of length 4'''

		assert len(number) == 4, 'Number must be a string of length 4'

		return 'LC'+number

	@_send
	def set_target_messier(self, number):
		'''set the current target to that defined by 
		the messier catalog object number
		The number must be a string of length 4'''

		assert len(number) == 4, 'Number must be a string of length 4'

		return 'LM'+number

	@_send
	def set_target_star(self, number):
		'''set the current target to that defined by 
		the star catalog object number
		The number must be a string of length 4'''

		assert len(number) == 4, 'Number must be a string of length 4'
		
		return "LS"+number

	@_send
	def _set_deepsky_catalog(self, catalog):
		'''set deepsky catalog helper method'''
		if type(catalog) is int:
			return "Lo"+str(catalog)

		return "Lo"+self.deepsky_catalogs[catalog]

	def set_deepsky_catalog(self, catalog):

		self._set_deepsky_catalog(catalog)
		self.recv(callback=self.resolve_catalog_availability('1','0'))	

	@_send
	def _set_star_catalog(self, catalog):
		'''set star catalog helper method'''
		if type(catalog) is int:
			return "Ls"+str(catalog)

		return "Ls"+self.star_catalogs[catalog]

	def set_star_catalog(self, catalog):

		self._set_star_catalog(catalog)
		self.recv(callback=self.resolve_catalog_availability('1','2'))	


	

class Telescope(ObjectInterface):

	DELAY = 0.01 # guaranteed by documentation NOTE: this means nothing here, goes in the SerialInterface

	def __init__(self, port, logfile=None):

		super().__init__(port, logfile)

		# The properties unique ot this object
		# Time {
		self._local_time = None
		self._siderial_time = None
		self._date = None
		self._utc_offset = None
		# }
		# Position {
		self._altitude = None
		self._azimuth = None
		self._longitude = None
		self._latitude = None
		# }
		# Pointing {
		self._ra = None
		self._dec = None
		# }
		# Motor {
		self._tracking_rate = None
		self._slew_rate_ra = ''
		self._slew_rate_dec = ''
		self._precision = None #TODO
		# }
		# Catalog {
		# } #TODO
		# Info {
		self._firmware_date = None
		self._firmware_number = None
		self._firmware_time = None
		self._product_name = None
		# }

		self.target = Target(port, logfile)
		self.library = ObjectLibrary(port, logfile)

	# Movement commands (Maybe make this it's own class or set of external funcs {

	@_send
	def move(self, direction):
		'''direction is either n, e, s, w'''
		direction = direction.lower() #NOTE: 'S' and 's' are different instructions, but this command is only movement
		assert len(direction) == 1, "Direction must be a single character but got: '{}'".format(direction)
		assert direction in 'nesw', "\n".join((
			"Must be of the following:",
			"  'n', 'e', 's', 'w'",
			"  but got: '{}'".format(direction)))

		return 'M'+direction

	@_send
	def slew_to_target(self):

		return 'MS'

	@_send	
	def halt(self, direction=''):
		'''direction is either n, e, s, w or empty string to stop all movement
		Might want to put some intermediate checks on this (though it is lower level) 
		to prevent the telescope from destroying itself'''
		direction = direction.lower()

		assert len(direction) in (0,1), "direction must be a single character or empty but got: '{}'".format(direction)
		assert direction in 'nesw', '\n'.join((
			"Must be of the following:",
			"  'n', 'e', 's', 'w', ''",
			"  but got: '{}'".format(direction)))

		return 'Q' + direction
	
	# } end movement commands

	# home position commands {

	@_send
	def park(self):

		return 'hP'

	@_send
	def sleep(self):

		return 'hN'

	@_send
	def wake(self):
		'''should check if it's asleep first'''
		return 'hW'	

	# }

	# Properties (Will probably be it's own container (a settings object), for now we'll use some properties) {
	# (Things that have both getters and setters in the interface)
	# (Might even need a seperate container for targets)

	# Time {

	@property
	def local_time(self):
		'''24 hour format'''

		self.getter('L', '_local_time')
		return self._local_time

	@property
	def siderial_time(self):

		self.getter('S', '_siderial_time')
		return self._siderial_time

	@property
	def date(self):

		self.getter('C', '_date')
		return self._date
	
	@property
	def utc_offset(self):

		self.getter('G','_utc_offset')
		return self._utc_offset

	# }
	# Position {

	@property
	def altitude(self):

		self.getter('A', '_altitude')
		return self._altitude

	@property
	def azimuth(self):

		self.getter('Z', '_azimuth')
		return self._azimuth
	
	@property	
	def longitude(self):

		self.getter('g','_longitude')
		return self._longitude

	@property
	def latitude(self):

		self.getter('t','_latitude')
		return self._latitude

	# }
	# Pointing {
	
	@property
	def declination(self):

		self.getter('D', '_dec')
		return self._dec

	@property
	def right_ascension(self):

		self.getter('R', '_ra')
		return self._ra

	# }
	# Motor {

	@property
	def tracking_rate(self):

		self.getter('T','_tracking_rate')
		return self._tracking_rate

	@property
	def slew_rate(self):
		'''format in <RA_rate, DEC_rate>'''

		return "".join(('<',self.slew_rate_ra,',',self.slew_rate_dec,'>'))

	@slew_rate.setter
	@_send
	def slew_rate(self, rate):
		'''rate is either an int from 0 to 4 or a character G, C, M, S'''
		if type(rate) is int:
			rate = {
				0:'G',
				1:'C',
				2:'M',
				3:'S'
			}[rate]

		return "R"+rate
		self._slew_rate_ra = rate
		self._slew_rate_dec = rate

		return 'R'+rate

	@property
	def slew_rate_ra(self):

		return self._slew_rate_ra

	@slew_rate_ra.setter
	@_send
	def slew_rate_ra(self, rate):
		'''rate is a floating point in degrees per second'''

		rate = "A{:02.1f}".format(rate)
		self._slew_rate_ra = rate[1:]
		
		return 'R'+rate

	@property
	def slew_rate_dec(self):

		return self._slew_rate_dec

	@slew_rate_dec.setter
	@_send
	def slew_rate_dec(self, rate):
		'''decte is a floating point in degrees per second'''

		rate = "E{:02.1f}".format(rate)
		self._slew_rate_dec = rate[1:]
		
		return 'R'+rate

	# }
	# Catalog {
	# } #TODO

	# Info {

	@property
	def firmware_date(self):

		self.getter('VD','_firmware_date')
		return self._firmware_date

	@property
	def firmware_number(self):

		self.getter('VN','_firmware_number')
		return self._firmware_number

	@property
	def firmware_time(self):

		self.getter('VT','_firmware_time')
		return self._firmware_time

	@property
	def product_name(self):

		self.getter('VP','_product_name')
		return self._product_name

	# }
	# }

def test():

	from serial import Serial
	import pdb
	TIMEOUT = 0
	#serial_port = Serial('/dev/ttyUSB0', timeout = TIMEOUT)
	#if not TIMEOUT:
	#	serial_port.nonblocking()
	# Defaults for LX200, these may need to be set accordingly for other scopes:
	#		parity: None
	#		bytesize: 8
	#		baudrate: 9600
	#		stopbits: 1
	#		rtscts: False
	#		dsrdtr: False
	with open("LX200.log",'w') as logfile:
		
		serial_port = SerialInterface(timeout=TIMEOUT, logfile=logfile)
		scope = Telescope(serial_port, logfile)
		scope.slew_rate = 'G'
		scope.slew_rate_ra = 1.23
		print(scope.slew_rate)
		pdb.set_trace() 

	pass
if __name__ == '__main__':
	pass
	test()
