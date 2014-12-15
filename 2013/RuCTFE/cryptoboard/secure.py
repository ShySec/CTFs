#!/usr/bin/python2
import time
import BaseHTTPServer
import urlparse
from Crypto.Cipher import AES
import binascii

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 4369

hx=binascii.hexlify
ux=binascii.unhexlify

messages = None
snapshotMessages = None

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def log_messages(self): pass

	def do_GET(self):
		global messages, snapshotMessages

		try:
			if messages is None:
				messages = {}
				try:
					with open("messages", "r") as fm:
						for line in fm.readlines():
							(id_hex, enc_hex, hash_hex, mes) = line.rstrip().split(" ")
							messages[(id_hex, enc_hex, hash_hex)] = mes
				except IOError:
					pass
				snapshotMessages = open("messages", "a")

			parsed_path = urlparse.urlparse(self.path)
			parsed_qs = urlparse.parse_qs(parsed_path.query)

			if parsed_path.path == "/list":
				result = self.list()
			elif parsed_path.path == "/get":
				id = parsed_qs["id"][0]
				sign = parsed_qs["sign"][0]
				enc = parsed_qs["enc"][0]
				result = self.get(id, sign, enc)
			elif parsed_path.path == "/put":
				mes = parsed_qs["mes"][0]
				result = self.put(mes)
			else:
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				return

			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()

			self.wfile.write(result)

		except Exception as e:
			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			return

	def get_random_hex(self, bytelen):
		with open("/proc/random", "rb") as f:
			return f.read(bytelen).encode("HEX")

	def list(self):
		return '%s %s'%(self.get_random_hex(8),self.get_random_hex(32))

	def get(self, id_hex, hash_hex, enc_hex):
		key = (id_hex,enc_hex,hash_hex)
		if key not in messages: return self.get_random_hex(32)
		return messages[key]

	def put(self, mes):
		id_hex = self.get_random_hex(16)
		enc_hex = self.get_random_hex(32)
		hash_hex = self.get_random_hex(32)

		messages[(id_hex,enc_hex,hash_hex)] = mes
		snapshotMessages.write(" ".join([id_hex, hash_hex, enc_hex, mes]) + "\n")
		snapshotMessages.flush()

		return " ".join([id_hex, hash_hex, enc_hex])


if __name__ == '__main__':
	print "Server init..."
	httpd = BaseHTTPServer.HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)

	print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
