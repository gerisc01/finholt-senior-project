# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db = db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()

db.define_table(
    auth.settings.table_user_name,
    Field('first_name', label='First Name', length=128, default=''),
    Field('last_name', label='Last Name', length=128, default=''),
    Field('email', label='Email',length=128, default='', unique=True),
    Field('password', 'password', length=512,            
          readable=False, label='Password'),
    Field('phone',label="Phone Number"),
    Field('registration_key', length=512,                # required
          writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,              # required
          writable=False, readable=False, default=''),
    Field('registration_id', length=512,                 # required
          writable=False, readable=False, default=''),
    Field('role', length=512, label="Role"))

custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.first_name.requires = \
  IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.last_name.requires = \
  IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.password.requires = [IS_STRONG(), CRYPT()]
custom_auth_table.email.requires = [
  IS_EMAIL(error_message=auth.messages.invalid_email),
  IS_NOT_IN_DB(db, custom_auth_table.email)]

## create all tables needed by auth if not custom tables
auth.define_tables()

## configure email
mail=auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
generalAuth = auth.id_group(role="General");
if auth.id_group(role="General")<=0:
    generalAuth = auth.add_group(role="General")
if auth.id_group(role="Admin")<=0:
    adminAuth = auth.add_group(role="Admin")
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
##auth.settings.everybody_group_id = 5

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

db.define_table("Project", Field('name','string'), Field('openDate','date'), Field('closedDate','date'), Field('projNum', 'integer'), Field('archived','boolean',readable=False, writable=False, default=False))

db.define_table("ProjectUser", Field('userRole','string'), Field('projectId','string'))

#db.define_table("User", Field('name','string'), Field('role','string'))          More stuff? Taken care of already?

db.define_table("CCD", Field('ccdNum','string'), Field('projectNum','string'), Field('file','upload'))

db.define_table("Submittal", Field('statusFlag','string'), Field('projectNum','string'), Field('assignedTo','string'), Field('submittal','upload'), Field('subType','string'))

db.define_table("RFI", Field('rfiNum','string'), Field('requestBy','string'), Field('dateSent','date'), Field('reqRefTo','string'), Field('drawingNum','integer'), Field('detailNum','integer'), Field('specSection','integer'), Field('sheetName','string'), Field('grids','string'), Field('sectionPage','integer'), Field('description','text'), Field('suggestion','text'), Field('reply','text'), Field('responseBy','date'), Field('responseDate','date'), Field('statusFlag','string'),Field('projectNum','string'))

db.define_table("ProposalRequest", Field('reqNum','string'), Field('amendNum','string'), Field('projectNum','string'), Field('subject','text'), Field('propDate','date'), Field('sentTo','string'), Field('cc','string'), Field('description','text'), Field('statusFlag','string'))

db.define_table("Proposal", Field('propNum','integer'), Field('propReqRef','integer'), Field('propDate','date'), Field('file','upload'),Field('projectNum','string'))

db.define_table("MeetingMinutes", Field('meetDate','date'), Field('file','upload'))

db.define_table("PhotoToken", Field('token','string'))

db.define_table("Photos", Field('projectNum','string'), Field('flickrURL','string'), Field('title','string'), Field('description','text'), Field('photo','upload', autodelete=True))
