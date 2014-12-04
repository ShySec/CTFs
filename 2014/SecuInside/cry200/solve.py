import time
import socket
import struct
import sys
import binascii
from PKI import PKI, PubKey, PrivKey
import pillow_reader

g_guestkey = '\xe1\xe7\xac\xa9\x19\x63\x0c\xf0'

l = 901924255379731264845598773404614424050302179361201900551370492885404232269980949480552626564987145191771090315436870704972059963780906410481831593467009
r = 378809047484150559420551156244892381913678443339678740198491628980093136457531188217807445914708130795016681935582189196123678346165963439434153143695999
g_pki_client = PKI(PubKey(l*r),PrivKey(l,r,l*r))
g_pki_server = PKI()

s2i = pillow_reader.s2i
b2s = pillow_reader.b2s
s2b = pillow_reader.s2b
i2s = pillow_reader.i2s

def read_files(s, authkey, filenames):
	cmd = 'cat ' + ' '.join(filenames)
	cmd = cmd.rstrip() + '\n'
	write(s, authkey + cmd)

	res = ''
	for _ in range(len(filenames)):
		res += read(s)
	return res

def exchange_key(s, n):
	print s.recv(1024)
	write(s, hex(n), False)
	serverN = int(read(s, False).replace('L',''),16)
	print 'server',serverN
	return PubKey(serverN)

def create_socket(host, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	return s

def write(s, data, with_encryption = True):
	if with_encryption:
		data = i2s(g_pki_server.encrypt(s2i(data)))
	size = struct.pack('<I', len(data))
	print 'sending',len(data),'bytes'
	send_data = size + data
	s.send(send_data)

def read(s, with_encryption = True):
	size_str = s.recv(4)
	size = struct.unpack('<I', size_str)[0]
	data = s.recv(size)
	if size != len(data):
		print('Wrong data size.\n')
		sys.exit(1)
	if with_encryption:
		data_int = s2i(data)
		data = i2s(g_pki_client.decrypt(data_int))
	if '[' in data:
		print binascii.hexlify(data[data.find('[')+1:data.find(']')])
	return data

def main():
	global s, g_pki_server
	if len(sys.argv) < 4:
		print('Usage> %s <host> <port> <filename> <optional:authkey>' % sys.argv[0])
		return 1
	host = sys.argv[1]
	port = sys.argv[2]
	filename = sys.argv[3]
	key = sys.argv[4] if len(sys.argv)>=5 else g_guestkey

	localN = 13
	s = create_socket(host, int(port))
	server_pubkey = exchange_key(s, localN)
	g_pki_server = PKI(pubkey_server)
	print(read_files(key, [filename]))

def cmd(data, token=g_guestkey):
	global g_pki_server,g_pki_client
	s = create_socket('219.240.37.153',5151)
	server_pubkey = exchange_key(s, g_pki_client.pubkey.n)
	#server_pubkey = PubKey(0x86e05276d3c364cd6157e23cd972e0a662dff9ebf9ade83eae022c292c767bcd6cf528c7f6ae98af2f7811d99c9e45e7e4e6f1b9841aabf89a84dd0673099b61L)
	g_pki_server = PKI(server_pubkey)
	write(s, token + data + '\n')
	print read(s)
	return s

def raw_cmd(data):
	global g_pki_server,g_pki_client
	s = create_socket('219.240.37.153',5151)
	server_pubkey = exchange_key(s, g_pki_client.pubkey.n)
	#server_pubkey = PubKey(0x86e05276d3c364cd6157e23cd972e0a662dff9ebf9ade83eae022c292c767bcd6cf528c7f6ae98af2f7811d99c9e45e7e4e6f1b9841aabf89a84dd0673099b61L)
	g_pki_server = PKI(server_pubkey)
	s.send(struct.pack('<I', len(data))+data)
	print read(s)
	return s

def raw(num):
	s= raw_cmd(i2s((s2i(binascii.unhexlify('1f59856dbbbe90995cf94975afd94dcf46bf2d16d8b8a3754685d3eb3765d6918462378a2f7e948182e84a857a25be057a122e9d65e32fb01a984f442e781fa02e8a4d2728b1a4c3ea3905aa95ab9fba7b7dfa3b39116d49c10d161725aa0beeac18b7a2a9c9d55a0bf6f1a2b2ca903eb15086995b2f77d77d3f01678708ee60'))*g_pki_server.encrypt(num))%g_pki_server.pubkey.n_sq))
	return s

if __name__ == '__main__':
	main()
