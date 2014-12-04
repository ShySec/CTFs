import math
from PrimeUtils import PrimeUtils

class PrivKey(object):
	def __init__(self, p, q, n):
		self.p = p
		self.q = q
		self.n = n
		self.l = (p - 1) * (q - 1)
		self.m = PrimeUtils.modinv(self.l, n)

class PubKey(object):
	def __init__(self, n):
		self.n = n
		self.n_sq = n * n
		self.g = n + 1

class PKI(object):
	def __init__(self, pubkey = None, privkey = None):
		if pubkey is not None:
			self.pubkey = pubkey
			self.privkey = privkey
		else:
			(self.privkey, self.pubkey) = self.gen_keypair()

	@staticmethod
	def gen_keypair(bits = 512):
		p = PrimeUtils.get_prime(bits // 2)
		q = PrimeUtils.get_prime(bits // 2)
		n = p * q
		return (PrivKey(p, q, n), PubKey(n))

	def encrypt(self, plain):
		while True:
			r = PrimeUtils.get_prime(int(round(math.log(self.pubkey.n, 2))))
			if r > 0 and r < self.pubkey.n:
				cipher = pow(self.pubkey.g, plain, self.pubkey.n_sq) * pow(r, self.pubkey.n, self.pubkey.n_sq) % self.pubkey.n_sq
				return cipher

	def decrypt(self, cipher):
		if not self.privkey is not None:
			raise AssertionError('Private key must be exist')
		if not self.pubkey is not None:
			raise AssertionError('Public key must be exist')
		pubkey = self.pubkey
		privkey = self.privkey
		plain = privkey.m * ((pow(cipher, privkey.l, pubkey.n_sq) - 1) // pubkey.n) % pubkey.n
		return plain
