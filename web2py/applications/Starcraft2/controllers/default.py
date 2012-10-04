# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import requests
import bs4
import re



r = requests.get('http://sc2pod.com/feeds/news.xml')
f = bs4.BeautifulSoup(r.text)



d = {}
d['1'] = []
d['2'] = ['20']
d['3'] = ['20','24']
d['4'] = ['20','24']
d['5'] = ['26']
d['6'] = ['26']
d['7'] = ['27']
d['8'] = ['30']
d['9'] = ['27']
d['10'] = ['27']
d['11'] = ['28']
d['12'] = ['29']
d['13'] = ['28']
d['14'] = ['31']
d['15'] = ['31']
d['16'] = ['31']
d['17'] = []
d['18'] = []
d['19'] = []
d['20'] = []
d['21'] = []
d['22'] = ['21']
d['23'] = ['20','24']
d['24'] = ['20']
d['25'] = ['24']
d['26'] = ['24']
d['27'] = ['24']
d['28'] = ['25']
d['29'] = ['25']
d['30'] = ['24']
d['31'] = ['27']
d['32'] = []
d['33'] = []
d['34'] = []
d['35'] = ['52']
d['36'] = ['52']
d['37'] = ['56']
d['38'] = ['57']
d['39'] = ['58']
d['40'] = ['59']
d['41'] = ['60']
d['42'] = ['41']
d['43'] = ['61']
d['44'] = ['61']
d['45'] = ['62']
d['46'] = ['64']
d['47'] = ['65']
d['48'] = ['47']
d['49'] = ['39']
d['50'] = []
d['51'] = []
d['52'] = []
d['53'] = ['52']
d['54'] = ['52']
d['55'] = ['53']
d['56'] = ['58']
d['57'] = ['52']
d['58'] = ['52']
d['59'] = ['52']
d['60'] = ['58']
d['61'] = ['58']
d['62'] = ['58']
d['63'] = ['58']
d['64'] = ['63']
d['65'] = ['63',]
d['66'] = ['36']
d['67'] = []
d['68'] = ['87']
d['69'] = ['86']
d['70'] = ['86','98']
d['71'] = ['86','98']
d['72'] = ['86','94','98']
d['73'] = ['93']
d['74'] = ['93','98']
d['75'] = ['93','95','98']
d['76'] = ['96']
d['77'] = ['96']
d['78'] = ['96','98']
d['79'] = ['96','98']
d['80'] = ['96','97','98']
d['81'] = ['78']
d['82'] = ['78']
d['83'] = []
d['84'] = []
d['85'] = []
d['86'] = ['84']
d['87'] = ['83']
d['88'] = ['87']
d['89'] = ['86']
d['90'] = ['86']
d['91'] = ['89']
d['92'] = ['89']
d['93'] = ['86']
d['94'] = ['86']
d['95'] = ['93']
d['96'] = ['93']
d['97'] = ['96']
d['98'] = []
d['99'] = []

@auth.requires_login()
def index():
	table = db(db.Unit)
	if len(table.select())<1:
		
		links = ['http://sc2armory.com/game/protoss/units','http://sc2armory.com/game/protoss/buildings','http://sc2armory.com/game/zerg/units','http://sc2armory.com/game/zerg/buildings','http://sc2armory.com/game/terran/units','http://sc2armory.com/game/terran/buildings']

		for alink in links:
			r = requests.get(alink)
			soup = bs4.BeautifulSoup(r.text)
			table = soup.find('table')

			rows = table.findAll('tr')

			for i in range(1,len(rows)):
				row = rows[i].find_all('td')
				m = re.search('(\w+)<',str(row[1]))
				n = re.search('\/img(.+)([0-9]{9,10})',str(row))
				alink = 'http://sc2armory.com/img'
				for item in n.groups(0):
					alink = alink +str(item)
				if 'terran' in alink:
					arace = 'terran'
				else:
					if 'zerg' in alink:
						arace='zerg'
					else:
						arace = 'protoss'
				db.Unit.insert(name=str(m.groups(0)[0]),link=str(alink),race=str(arace))
			
	"""
	example action using the internationalization operator T and flash
	rendered by views/default/index.html or views/generic.html
	"""

	return dict(message=db(db.Unit).select(),feed=f)

def user():
	"""
	exposes:
	http://..../[app]/default/user/login
	http://..../[app]/default/user/logout
	http://..../[app]/default/user/register
	http://..../[app]/default/user/profile
	http://..../[app]/default/user/retrieve_password
	http://..../[app]/default/user/change_password
	use @auth.requires_login()
		@auth.requires_membership('group name')
		@auth.requires_permission('read','table name',record_id)
	to decorate functions that need access control
	"""
	return dict(form=auth())


def download():
	"""
	allows downloading of uploaded files
	http://..../[app]/default/download/[filename]
	"""
	return response.download(request,db)


def call():
	"""
	exposes services. for example:
	http://..../[app]/default/call/jsonrpc
	decorate with @services.jsonrpc the functions to expose
	supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
	"""
	return service()


@auth.requires_signature()
def data():
	"""
	http://..../[app]/default/data/tables
	http://..../[app]/default/data/create/[table]
	http://..../[app]/default/data/read/[table]/[id]
	http://..../[app]/default/data/update/[table]/[id]
	http://..../[app]/default/data/delete/[table]/[id]
	http://..../[app]/default/data/select/[table]
	http://..../[app]/default/data/search/[table]
	but URLs must be signed, i.e. linked with
	  A('table',_href=URL('data/tables',user_signature=True))
	or with the signed load operator
	  LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
	"""
	return dict(form=crud())

def build():
	
	message= db(db.Unit.race==request.vars.race).select().as_list()
	numlist = []
	auxNumList = []
	for i in range(5,151):
		numlist.append(i)
		auxNumList.append(i)
	alist= []
	for unit in message:
		alist.append(unit['name'])
	alist.sort()
	if request.vars.Unit: # see if new Unit is passed in
		numlist = filter(lambda a:a>int(request.vars.Supply),numlist)
		mybuild = db(db.Build.id==request.vars.build).select().first()
		neededUnits=False #checking if required units are met for selected Unit
		failUnit= None
		reqUnits=0
		checkUnit = db(db.Unit.name==request.vars.Unit).select().first()
		for item in d[str(checkUnit.id)]:
			if checkIt(item,request.vars.unit):
				reqUnits +=1
			else:
				failUnit = db(db.Unit.id==item).select().first()
		if len(d[str(checkUnit.id)])==reqUnits: # check that number of requried units matches the number of required units listed in the dictionary.
			neededUnits=True
			
		if neededUnits==True:
			
			form = SQLFORM.factory(Field('Unit',requires=IS_IN_SET(alist),default=alist[0]),Field('Supply',requires=IS_IN_SET(numlist),default=numlist[0]),hidden=dict(race=request.vars.race,unit=request.vars.unit+request.vars.Unit+'||',supply=request.vars.supply+request.vars.Supply+'||',build=request.vars.build,buildname=request.vars.buildname))
			unitlist = request.vars.unit +request.vars.Unit+'||'
			supplylist = request.vars.supply + request.vars.Supply + '||'
			mybuild.update_record(unitList=unitlist)
			mybuild.update_record(supplyList=supplylist)
		else:
			auxSupply = request.vars.supply
			auxSupply = auxSupply.split('||')
			auxSupply = filter(lambda a:a!='',auxSupply)
			correctSupply= 5
			if len(auxSupply)>0:
				correctSupply = auxSupply[-1]
			auxNumList = filter(lambda a:a>int(correctSupply),auxNumList)
			form = SQLFORM.factory(Field('Unit',requires=IS_IN_SET(alist),default=alist[0]),Field('Supply',requires=IS_IN_SET(auxNumList)),hidden=dict(race=request.vars.race,unit=request.vars.unit,supply=request.vars.supply,build=request.vars.build,buildname=request.vars.buildname))
			unitlist = request.vars.unit
			supplylist = request.vars.supply
			response.flash="Need a "+ str(failUnit.name)
		
	else:
		buildNum=db.Build.insert(name=request.vars.buildname,userid=auth.user.id,unitList='',supplyList='')
		form = SQLFORM.factory(Field('Unit',requires=IS_IN_SET(alist),default=alist[0]),Field('Supply',requires=IS_IN_SET(numlist),default=numlist[0]),hidden=dict(race=request.vars.race,unit=request.vars.unit,supply=request.vars.supply,build=buildNum,buildname=request.vars.buildname))
		unitlist=''
		supplylist=''
		
	unitlist = unitlist.split('||')
	unitlist = filter(lambda a:a!='',unitlist)
	supplylist = supplylist.split('||')
	supplylist = filter(lambda a:a!='',supplylist)
	for i in range(len(unitlist)):
		row = db(db.Unit.name==unitlist[i]).select()
		unitlist[i] = row.as_list()
	return dict(form=form,unitlist=unitlist,supplylist=supplylist,feed=f)
	
def mybuild():
	buildUnits = []
	buildSupplies = []
	buildNames=[]
	buildIDs=[]
	builds = db(db.Build.userid==auth.user.id).select()
	for build in builds:
		buildIDs.append(build.id)
		buildNames.append(build.name)
		unitlist = build.unitList.split('||')
		unitlist = filter(lambda a:a!='',unitlist)
		supplylist = build.supplyList.split('||')
		supplylist = filter(lambda a:a!='',supplylist)
		buildUnits.append(unitlist)
		buildSupplies.append(supplylist)
	return dict(buildUnits=buildUnits,buildSupplies=buildSupplies,buildNames=buildNames,buildIDs=buildIDs,feed=f)
	
def delete():
	query = db(db.Build.id==request.args(0).replace('_',' ')).select().first()
	remove = db(db.Build.id==query).delete()
	if remove:
		 redirect(URL('Starcraft2','default','mybuild'))
	return dict(remove=remove)
	
def checkIt(unitnum, unitList):
	unit = db(db.Unit.id==unitnum).select().first()
	if unit.name in unitList:
		return True
	else:
		return False

