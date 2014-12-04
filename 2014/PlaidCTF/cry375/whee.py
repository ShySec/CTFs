from hashlib import sha512,sha1
import random
import binascii
hx = binascii.hexlify
ux = binascii.unhexlify
import pickle

KEY = [0, 0]

M = 12
N = 24 # M * 2
K = 24 # N = M * 2
numrounds = 2 ** 24 # Protip: would not bruteforce this if I were you.

def genTable(seed="Function shamelessly stolen from bagre"):
  fSub = {}
  i = 0
  prng = sha512()
  prng.update(seed)
  seed = prng.digest()
  cSeed = ""
  for x in xrange(2048):
    cSeed+=prng.digest()
    prng.update(str(x)+prng.digest())
  fCharSub = [0]*(2**M)
  gCharSub = [0]*(2**M)
  unused = range(2**M)
  for x in xrange(0,2**(M+1),2):
    curInd = (ord(cSeed[x]) + (ord(cSeed[x + 1]) << 8)) % len(unused)
    toDo = unused[curInd]
    del unused[curInd]
    fSub[x / 2] = toDo
  return fSub

f1 = genTable("Function shamelessly stolen from bagre")
f2 = genTable("Good thing I didn't also steal the seed!")
f2i = dict([(v,k) for k,v in f2.items()])
f1i = dict([(v,k) for k,v in f1.items()])

def gen_key():
  k0 = random.randint(0,2**(K/2)-1)
  k1 = random.randint(0,2**(K/2)-1)
  return [k0, k1]

#KEY = gen_key()
KEY = [4024,3706]

def F1(s, k): return f1[s^k]
def F2(s, k): return f2[s^k]
def F1i(s, k): return f1i[s^k]
def F2i(s, k): return f2i[s^k]

def encrypt_block(plaintext, key):
  txt = plaintext
  l, r = (txt >> M) & ((1 << M) - 1), txt & ((1 << M) - 1)
  for x in xrange(numrounds):
    if x % 2 == 0:
      l1,r1 = r, l ^ F1(r, key[0])
      l, r = l1, r1
    else:
      l1,r1 = l, l ^ F2(r, key[1])
      l, r = l1, r1
  txt = l << M | r
  return txt

def decrypt_block(ciphertext, key):
  txt = ciphertext
  l, r = (txt >> M) & ((1 << M) - 1), txt & ((1 << M) - 1)
  for x in xrange(numrounds-1,-1,-1):
    if x % 2 == 0:
      l1,r1 = r ^ F1(l, key[0]), l
      l, r = l1, r1
    else:
      l1,r1 = l, f2i[l ^ r]^key[1]
      l, r = l1, r1
  txt = l << M | r
  return txt

def extract(s):
  c = 0
  for x in s:
    c = (c << 8) | ord(x)
  return c

def intract(n):
  s = []
  while n > 0:
    s.append(chr(n & 0xff))
    n = n >> 8
  return ''.join(s[::-1])

def get_blocks(txt):
  n = N / 8 # 3
  if len(txt) % n != 0:
    txt += '\x00' * (n - len(txt) % n)
  block_strs = [txt[i*n:i*n+n] for i in range(len(txt) / n)]
  return [extract(s) for s in block_strs]

def unblocks(l):
  z = [intract(x) for x in l]
  s = ''.join(z)
  s = s.strip('\x00')
  return s

def encrypt(plaintext,key=KEY):
  print str(key)
  blocks = get_blocks(plaintext)
  out = [encrypt_block(block, key) for block in blocks]
  return unblocks(out)

def decrypt(ciphertext,key=KEY):
  blocks = get_blocks(ciphertext)
  out = [decrypt_block(block, key) for block in blocks]
  return unblocks(out)
