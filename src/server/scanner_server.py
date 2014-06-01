#!/usr/bin/python

import os
import json
import zmq
from zmq.eventloop import zmqstream,ioloop
ioloop.install()

import pyinsane.abstract as pyinsane
import pyinsane.rawapi as rawapi

class ScannerServer():

	def __init__(self):
		self.context = zmq.Context()
		self.pull = self.context.socket(zmq.PULL)
		self.pull.bind("tcp://*:8890")
		self.pub = self.context.socket(zmq.PUB)
		self.pub.bind("tcp://*:8891")
		self.loop = ioloop.IOLoop.instance()
		self.stream = zmqstream.ZMQStream(self.pull)
		self.stream.on_recv(self.handle_msg)
		self.device = pyinsane.get_devices()[0]


	def handle_msg(self, message):
		try:
			msg = json.loads(message[0])
			print msg
			output = {"pages":0,
		          "files":[]}
			if msg['type'] == 'scan':
				self.device.options['resolution'].value = 150
				self.device.options['source'].value = msg['source']
				if msg['source'] == 'ADF':
					multiple = True
				else:
					multiple = False
				scan_session = self.device.scan(multiple=multiple)
				try:
					while True:
						try:
							scan_session.scan.read()
						except EOFError:
							pass
				except StopIteration:
					output["pages"] = len(scan_session.images)
				for idx in xrange(0, len(scan_session.images)):
					image = scan_session.images[idx]
					file_name = '{}{}.png'.format(msg["name"],
	                         idx)
					image.save(file_name)
					output["files"].append(os.path.abspath(file_name))
				print output
				self.pub.send_multipart(['scan',
			                         json.dumps(output)])
		except ValueError:
			print "Invalid JSON message"
		except Exception as ex:
			print "Error: {}".format(ex.message)
def main():
	gen = ScannerServer()
	ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
