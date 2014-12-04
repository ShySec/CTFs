import whee
import binascii

ux = binascii.unhexlify
hx = binascii.hexlify

def deblock(data):
	if len(data)%6: return []
	return [data[i:i+6] for i in xrange(0,len(data),6)]

def getKeysets(filename):
	import re
	data=open(filename).read()
	keysets=re.findall('key ([^\n]+)\n([^ ]+) = ([^\n]+)\n',data)
	print 'loaded',len(keysets),'keysets'
	rval={}
	for keyset in keysets:
		key,ptxt,ctxt = keyset
		ptxt,ctxt = deblock(ptxt),deblock(ctxt)
		rval[key] = rval.get(key,set()).union(set(zip(ptxt,ctxt)))

	return rval

def splitLR(value):    return int(value[:3],16),int(value[3:],16)
def splitKP(keypair):  return splitLR(keypair[0]),splitLR(keypair[1])

def getSlidPairs(flag,keyset):
	import itertools
	possibleKeys = []
	for m0,m1 in itertools.permutations(keyset, 2):
		(mp0l,mp0r),(mc0l,mc0r) = splitKP(m0)
		(mp1l,mp1r),(mc1l,mc1r) = splitKP(m1)
		if mp0r != mp1l: continue # not a pair
		if mc0r != mc1l: continue # not a pair
		keys = []
		for k0 in xrange(4096):
			for k1 in xrange(4096):
				if mp1r != mp0r ^ whee.f2[mp0l ^ whee.f1[mp0r ^ k0] ^ k1]: continue
				if mc1r != mc0r ^ whee.f2[mc0l ^ whee.f1[mc0r ^ k0] ^ k1]: continue
				if whee.encrypt(ux(m0[0]),[k0,k1]) != ux(m0[1]): continue
				if whee.encrypt(ux(m1[0]),[k0,k1]) != ux(m1[1]): continue
				print flag,m0,m1,k0,k1
				print 'flag? ',whee.decrypt(ux(flag),[k0,k1])

def tryAllSlidPairs(filename):
	keysets = getKeysets(filename)
	for key in keysets:
		getSlidPairs(key,keysets[key])

tryAllSlidPairs('output.txt')
