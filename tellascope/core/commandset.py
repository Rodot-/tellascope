'''
Module for abstracting the serial command set for the lx2000 telescope

Commands are grouped with the following types:

	get: commands that get some attribute
	arg: command with arguments

'''

TIMEOUT = 0.1 #Telescope Timeout

class Command:
	'''base class for serial command'''

	def __init__(self, cmd_base, ser):

		self.base = cmd_base
		self.command = ''
		self.ser = ser

	def __call__(self, *args):
		'''callable function, highest level abstraction'''
		pass

	def build(self, *args):
		'''Create the full command here, overwrite this method'''
		pass

	def __str__(self):
		'''Prepare the command for sending, what is sent to the serial device'''
		return self.command.join(':#')

	def send(self, *args):
		'''send command to the serial device'''
		self.build(*args)
		self.ser.write(str(self))

	def recv(self):
		'''recieve command from serial device'''
		return self.ser.read_all()


class GetCommand(Command):
	'''Command that only gets a value'''

	def __init__(self, cmd_base, ser):

		Command.__init__(self, cmd_base, ser)
		self.command = self.base

	def __call__(self):
	
		self.send()
		time.sleep(TIMEOUT)
		return self.recv()	

	def build(self):
		'''just use the base as the command'''
		return self.command

