import re
import sys
import time
import struct
import socket
import binascii
import subprocess

def connect(host,port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	s.connect((host,port))
	return s

def recvtil(s,trigger,display=True,blocking=True,timeout=None):
	data = ''
	otimeout = s.gettimeout()
	oblocking = True # default until s.getblocking() exists
	if timeout != otimeout: s.settimeout(timeout)
	if blocking != oblocking: s.setblocking(blocking)
	try:
		while trigger not in data:
			tmp = s.recv(4096)
			if not len(tmp): break
			if display: print tmp
			data += tmp
	except socket.error as e:
		if e.errno == socket.errno.EWOULDBLOCK: pass
		else: raise # something went wrong
	finally:
		if blocking != oblocking: s.setblocking(oblocking)
		if timeout != otimeout: s.settimeout(otimeout)
	return data

def cmd(s,option,*args,**kwargs):
	data = recvtil(s,'6) quit',display=False,**kwargs)
	s.send(str(option)+'\n')
	for arg in args:
		if type(arg) == tuple:
			prompt,value = arg
			data += recvtil(s,prompt,display=False)
			s.send('%s\n'%value)
		else:
			s.send(arg+'\n')
	return data

def cmdSetBet(s,value,blocking=False,**kwargs):    return cmd(s,2,('Please pick your bet amount',          value),blocking=blocking,**kwargs)
def cmdSetOdds(s,value,blocking=False,**kwargs):   return cmd(s,1,('Please pick odds',                     value),blocking=blocking,**kwargs)
def cmdPlayRound(s,nonce,blocking=False,**kwargs): return cmd(s,3,('Okay, send us a nonce for this round!',nonce),blocking=blocking,**kwargs)

def cmdGetBalance(s,blocking=False,**kwargs):
	cmd(s,4,blocking=blocking,**kwargs)
	data = recvtil(s,'Your current balance is $',display=False)
	return int(re.findall('Your current balance is \$(\d+)',data)[0])

def extractHash(data):
	hashes = re.findall('Too bad, we generated (\d+), not 0',data)
	if not len(hashes): return 0
	return int(hashes[0])

def playRound(s, data, **kwargs):
	cmdPlayRound(s,data,**kwargs)
	return extractHash(recvtil(s,'====================',False))

def lengthExtensionAttack(known, knownHash, suffix, keylen=16, debug=False):
	known += '\n'
	suffix += '\n'
	cmd = './hashpump -d \'%s\' -s %032x -a \'%s\' -k %d'%(known,knownHash,suffix,keylen)
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	p.wait()
	if debug: print cmd
	data = p.communicate()[0]
	extensionHash,extensionData = re.findall('([0-9a-f]+)\n(.+)',data,re.M)[0]
	extensionData = extensionData.decode('string-escape')[:-1] # drop newline
	return extensionData,int(extensionHash,16)

def solveForOriginal(known,knownHash,suffix,extHash,knownBits=100,keylen=16,debug=False):
	counter = 0
	known += '\n'
	suffix += '\n'
	unknownBits = keylen*8 - knownBits
	print 'brute forcing original hash (%d bits)'%unknownBits
	cmd = './recover "%s" %032x "%s" %032x'%(known,knownHash,suffix,extHash)
	if debug: print cmd
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	while p.poll() is None:
		sys.stdout.write('.')
		sys.stdout.flush()
		time.sleep(0.5)
	sys.stdout.write('\n')
	data = p.communicate()
	return int(data[0],16)

def pickOdds(givenHash):
	for i in xrange(32):
		if givenHash & (1<<i): return i
	raise Exception('technically possible, but probably an error')

def shell(lvars, gvars=None, banner=None):
	import code
	namespace = dict(gvars,**lvars)
	code.interact(banner,local=namespace)

def netcat(s):
	import sys
	import select
	print '--- netcat mode enabled ---'
	while True:
		rfdl, wfdl, efdl = select.select([s, sys.stdin], [], [], None)
		if sys.stdin in rfdl:
			data = sys.stdin.readline()
			if data == '!quit': break
			if not data: continue
			s.send(data+'\n')
		if s in rfdl:
			data = s.recv(4096)
			if not data:
				print 'netcat canceled: socket disconnected'
				break
			sys.stdout.write(data)
	print '--- netcat mode disabled ---'

if __name__ == '__main__':
	host,port='54.197.195.247',4321
	s = connect(host,port)
	print 'learning w/ free play'
	cmdSetBet(s,   0) # bet = 0 (free play)
	cmdSetOdds(s,100) # odds = 100 (max leak)

	known = 'ShySecurity' # anything, but not pure hex
	knownHash = playRound(s, known) # partial hash (modulo 2^100)
	print 'received partial known-hash   %032x'%knownHash

	extStr,extHash = lengthExtensionAttack(known,knownHash,known)
	extHash = playRound(s, extStr, blocking=False) # get the next partial hash
	print 'received partial related-hash %032x'%extHash

	#cmd(s,5,blocking=False)
	#print recvtil(s,'nonce',False)

	realHash = solveForOriginal(known,knownHash,known,extHash)
	print 'recovered original known-hash %032x'%realHash

	balance = 1000
	print 'playing for money now'
	for i in xrange(1<<32):
		suffix = '%x'%i
		testStr,testHash = lengthExtensionAttack(known, realHash, suffix)
		print 'generated full-hash %032x for "%s"'%(testHash,suffix)
		odds = pickOdds(testHash)
		if not odds:
			print 'odds 0 # skipping'
			continue
		print 'betting %d with odds %d'%(balance,odds)
		cmdSetBet(s,balance)
		cmdSetOdds(s,  odds)

		playRound(s,testStr)
		balance *= 1<<odds
		print 'balance',balance
		if balance >= 1000000000:
			s.send('\n')
			print recvtil(s,'Here\'s a key:',blocking=False)
			break

	netcat(s)
	shell(locals(),globals())
