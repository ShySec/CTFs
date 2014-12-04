import re
import socket
import hashlib
import binascii
import stdlib.ctf.Keygen as keygen

hx = binascii.hexlify
ux = binascii.unhexlify

def lookup(key):
	import pickle
	db = pickle.loads(open('hashes.db').read())
	if key not in db:
		db[key] = collide(key)
		open('hashes.db','wb').write(pickle.dumps(db))
	return db[key]

def collide(key):
	try:
		keygen.crack(keygen.bfs(keygen.alphanum()+'+/',5,minDepth=5,prefix=key), validate)
	except keygen.ReturnSuccess as r:
		return r.args[1]
	raise Exception('wat?')

def validate(key):
	if len(key) < 5: return False
	return hashlib.sha1(key).hexdigest().endswith('ffffff')

def connect(hostname, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	s.connect((hostname, port))
	return s

def recvtil(s,trigger,display=True):
	data = ''
	while trigger not in data:
		tmp = s.recv(4096)
		if not len(tmp): break
		if display: print tmp
		data += tmp
	return data

def decrypted(instr,outstr):
	blockdb = pickle.loads(open('blocks.db').read())
	inblocks = [instr[i:i+3] for i in xrange(0,len(instr),3)]
	outblocks = [outstr[i:i+6] for i in xrange(0,len(outstr),6)]
	blocks = dict(zip(inblocks,outblocks))
	for block in blocks: blockdb[block]=blocks[block]
	open('blocks.db','wb').write(pickle.dumps(blockdb))
	print len(blockdb),'decrypted blocks'

def goEncrypt(host,port,ptxt):
	s = connect(host,port)
	data = recvtil(s,'ends in ffffff\n',False)
	prefix = re.findall('starting with ([^,]+), of length 21',data)[0]
	proof = lookup(prefix)
	s.send(proof+'\n')
	data = recvtil(s,'Send your encryption string:',False)
	key = re.findall('^([^\n]+)\nSend your encryption',data,re.M)[0]
	print 'key',key
	s.send(ptxt+'\n')
	ctxt = s.recv(4096)
	s.shutdown(socket.SHUT_RDWR)
	print ptxt,'=',ctxt
	return key,ptxt,ctxt

def deblock(data):
	return [data[i:i+6] for i in xrange(0,len(data),6)]

def swapgen():
	for lval in keygen.bfs(keygen.digits(),3,minDepth=3):
		for rval in keygen.bfs(keygen.digits(),3,minDepth=3,debug=False):
			yield rval+lval

if __name__ == '__main__':
	gen = swapgen()
	host,port='54.82.75.29',8193
	while True:
		key,ptxt,ctxt = goEncrypt(host,port,''.join([gen.next() for i in xrange(40)]))
