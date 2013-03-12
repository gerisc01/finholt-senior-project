# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

#import oauth
#import httplib2 
#import urllib2
import flickrapi
#import ctypes


#Flickr API keys
KEY = '614fd86a34a00d38293c7e803d14c3ab'
SECRET_KEY = 'ad86826c3187eb4d'
USER_ID = '93142072@N05'


if not db(db.PhotoToken).isempty():
    tok = (db.PhotoToken(db.PhotoToken.id>0)).token
    flickr = flickrapi.FlickrAPI(KEY, SECRET_KEY, token = tok)     #create a flickr object
else:
    flickr = flickrapi.FlickrAPI(KEY, SECRET_KEY)

if not db(db.PhotoToken).isempty():
    # We have a token, but it might not be valid
    try:
        flickr.auth_checkToken()
    except flickrapi.FlickrError:
        db(db.PhotoToken.id > 0).delete()
if db(db.PhotoToken).isempty():                #we don't have the token yet
    if request.vars.frob:                      #if the frob is in the request 
        db.PhotoToken[0] = {"token" : flickr.get_token(request.vars.frob)}    #insert a new row into the database with the token
    else:
        url = flickr.web_login_url('write')    #get the url to go to in order to authenticate
        redirect(url)                          #redirect to that website


if auth.user != None:
    record = auth.user.id     #Gets the info for the current user
    myProfileForm = SQLFORM(db.auth_user, record, showid=False, labels={'first_name':'First Name', 'last_name':'Last Name', 'email':'E-mail', 'phone':'Phone Number', 'password':'New Password'}, fields = ['first_name','last_name','email','phone'],_id="profileForm")
else: 
    myProfileForm = SQLFORM(db.auth_user, showid=False, labels={'first_name':'First Name', 'last_name':'Last Name', 'email':'E-mail', 'phone':'Phone Number', 'password':'New Password'}, fields = ['first_name','last_name','email','phone'],_id="profileForm")


projects = db(db.Project.archived == False).select()

header = DIV(A(IMG(_src=URL('static','images/bluebannertext.jpg')), _href=URL('default','index')), _id="header")
footer = DIV(A("Home Page", _href=URL('default','index')), _id="footer")
css = "/SeniorProject/static/css/bluestyle.css"

def uploadPhotoToFlickr(photoForm):
    #MessageBox = ctypes.windll.user32.MessageBoxA
    #MessageBox(None, str(photoForm.vars), 'Title', 0)
    
    #Get the info from the submitted photo form
    photoWeb2pyId = photoForm.vars.id
    projNum = photoForm.vars.projectNum
    title = photoForm.vars.title
    descr = photoForm.vars.description
    name = "applications/SeniorProject/uploads/" + photoForm.vars.photo
    
    #Upload the photo to flickr and get the id of the photo in order to construct the url of the photo
    idElement = flickr.upload(filename=name, title=title, description=descr)
    id = idElement.find('photoid').text
    flickrUrl =  "http://www.flickr.com/photos/"+USER_ID+"/"+str(id)+"/"  

    #Delete the corresponding row in our database (because we don't want to store the actual photo here)
    db(db.Photos.id == photoWeb2pyId).delete()
    
    #Create a new row in our database with all the same info as the deleted row, but without the photo file
    db.Photos.insert(projectNum=projNum, flickrURL=flickrUrl, title=title, description=descr)


@auth.requires_login()
def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """    
     
    response.flash = "Welcome " + auth.user.first_name + "!"
    return dict(
                projects=projects,
                myProfileForm=myProfileForm,
                header=header,
                footer=footer,
                css=css)

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
    return dict(form=auth(), header=header, footer=footer, css=css)


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
    return dict(form=crud(), css=css, footer=footer)

@auth.requires_membership('Admin')
def register():
    form = SQLFORM(db.auth_user)
    if form.validate():
        admin_user = auth.user
        auth.get_or_create_user(form.vars)
        auth.add_membership(auth.id_group(role="General"),auth.user_id) 
        auth.user = admin_user
        redirect(URL('default','manageusers'))
    return dict(form=form, header=header, footer=footer, css=css)
    #admin_auth = session.auth
    #auth.is_logged_in = lambda: False
    #def post_register(form):
    #    auth.add_membership(auth.id_group(role="General"),auth.user_id) 

     #   session.auth = admin_auth
     #   auth.user = session.auth.user
    #auth.settings.register_onaccept = post_register
    #return dict(form=auth.register())

@auth.requires_login()
@auth.requires_membership('Admin')
def changepermissions():
     rows=db(db.auth_user.id>0).select() 
     #db.auth_user.id.represent=lambda id: DIV(id,SELECT(str(db(db.auth_group.id==db(db.auth_membership.user_id==id).select().first().group_id).select().first().role), XML(getOtherRoles(str(db(db.auth_group.id==db(db.auth_membership.user_id==id).select().first().group_id).select().first().role))), _name='%i'%id)) # INPUT (_type='checkbox',_name='%i'%id)) 
     db.auth_user.id.represent=lambda id: SELECT(getUserRole(id), XML(getOtherRoles(id)), _name='%i'%id) # INPUT (_type='checkbox',_name='%i'%id)) 
     table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Change Permission","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit')) 
     if table.accepts(request.vars): 
        for item in request.vars.keys():
            if item.isdigit():
                if not auth.has_membership(user_id=int(item), role=request.vars[item]):
                    if auth.has_membership(user_id=int(item), role=getUserRole(int(item))): #in case they are in their individual user group. We shoudl only delete them from the group we are in if they are switching from General to Admin or vice versa.
                        
                        auth.del_membership(auth.id_group(role=getUserRole(int(item))),int(item))
                    auth.add_membership(auth.id_group(role=request.vars[item]),int(item)) 
                    

        redirect(URL('default','manageusers'))
     return dict(table=table, footer=footer, header=header, css=css)

@auth.requires_login()
@auth.requires_membership('Admin')
def deleteusers():
     rows=db(db.auth_user.id>0).select() 
     db.auth_user.id.represent=lambda id: DIV(id,INPUT (_type='checkbox',_name='%i'%id)) 
     table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Remove User","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit')) 
     if table.accepts(request.vars): 
        for item in request.vars.keys():
            if item.isdigit():
                db(db.auth_user.id == int(item)).delete()
        redirect(URL('default','deleteusers'))
            # or so something not sure what you want to do 
     return dict(table=table, footer=footer, header=header,css=css)
 
@auth.requires_login()    
@auth.requires_membership('Admin')
def createproject():
    form = SQLFORM(db.Project, labels={'openDate':'Open Date', 'closedDate':'Closed Date', 'projNum':'Project Number'})
    if form.process().accepted:
       response.flash = 'form accepted'
    elif form.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'please fill out the form'
    return dict(form=form, footer=footer, header=header, css=css)

@auth.requires_login()   
@auth.requires_membership('Admin')
def manageprojects():
    table = None
    rows = db(db.Project.archived == False).select()
    db.Project.id.represent=lambda id: DIV(id,INPUT (_type='checkbox',_name='%i'%id)) 
    #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc:     IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
    table = FORM(SQLTABLE(rows,columns=["Project.id","Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.id":"Archive","Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #"}),INPUT(_type='submit'))
    if table.accepts(request.vars):
        for pID in request.vars.keys():
            if pID.isdigit():
                db(db.Project.id ==int(pID)).update(archived=True)
        redirect(URL('default','manageprojects'))
    return dict(table=table, footer=footer, header=header,css=css)
    
@auth.requires_login()
@auth.requires_membership('Admin')

def archiveprojects():
    table = None
    rows = db(db.Project.archived == True).select()
    #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc:     IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
    table = SQLTABLE(rows,columns=["Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #", "Project.archived":"Archived"})
    return dict(table=table, footer=footer, header=header, css=css)

def showform():
    displayForm = request.vars.displayForm
    form = None
    if displayForm == "CCD":
        form = SQLFORM(db.CCD, labels={'ccdNum':'CCD #','projectNum': "Project #"})
        rows = db(db.CCD.projectNum == str(request.vars.projectNum)).select()
        form.vars.ccdNum = len(rows) + 1
    elif displayForm == "RFI":
        db.RFI.reqRefTo.requires = IS_IN_DB(db, 'auth_user.first_name')
        form = SQLFORM(db.RFI, labels={'rfiNum':'RFI #','projectNum':"Project #", 'requestBy':'Request by', 'dateSent':'Date Sent', 'reqRefTo':'Request Referred to', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':'Contractor\'s Suggestion', 'responseBy':'Need Response By'}, fields=['rfiNum','projectNum','requestBy', 'dateSent', 'reqRefTo', 'drawingNum', 'detailNum', 'sheetName', 'grids', 'specSection', 'sectionPage', 'description', 'suggestion', 'responseBy'])
        rows = db(db.RFI.projectNum == str(request.vars.projectNum)).select()
        form.vars.rfiNum = len(rows) + 1
        form.vars.requestBy = auth.user.first_name
        form.vars.statusFlag = "Outstanding"            
    elif displayForm == "Submittal":
        db.Submittal.subType.requires = IS_IN_SET(['Samples','Shop Drawing','Product Data'])
        db.Submittal.assignedTo.requires = IS_IN_DB(db, 'auth_user.first_name')
        db.Submittal.statusFlag.requires = IS_IN_SET(['Approved','Resubmit','Approved with Comments','Submitted for Review'])
        form = SQLFORM(db.Submittal, labels={'statusFlag':'Status Flag', 'projectNum':'Project Number', 'subType':'Submittal Type','assignedTo':'Assigned to'}) 
    elif displayForm == "ProposalRequest":  
        db.ProposalRequest.statusFlag.requires = IS_IN_SET(['Open','Closed'])     
        form = SQLFORM(db.ProposalRequest, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'statusFlag':'Status', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'})
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        form.vars.reqNum = len(rows) + 1
    elif displayForm == "Proposal":
        therows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select(db.ProposalRequest.reqNum)
        alist = therows.as_list()
        blist = []
        for item in alist:
            blist.append(item['reqNum'])
        db.Proposal.propReqRef.requires = IS_IN_SET(blist)
        form = SQLFORM(db.Proposal, labels={'propNum':'Proposal #', 'propReqRef':'Proposal Request Reference #', 'projectNum':'Project Number', 'propDate':'Proposal Date'})
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        form.vars.propNum = len(rows) + 1
    elif displayForm == "MeetingMinutes":
        form = SQLFORM(db.MeetingMinutes, labels={'meetDate':'Meeting Date'})
    elif displayForm == "Photo":                         
        form = SQLFORM(db.Photos, labels={'projectNum':'Project Number', 'title':'Title', 'description':'Description', 'photo':'Photo'}, fields = ['projectNum','title','description','photo'])

    if form != None:
        if form.process().accepted:
            response.flash = T('form accepted')
            if displayForm == "Photo":
                uploadPhotoToFlickr(form)
        elif form.errors:
            response.flash = 'form has errors'
        else:
            response.flash = 'please fill out the form'
            
    return dict(displayForm=displayForm,
                form=form,
                myProfileForm=myProfileForm,
                projects=projects,
                footer=footer,
                header=header,
                css=css)

@auth.requires_login()
def formtable():
    formType = request.vars.formType
    table = None
    image = None
    fullTable = True
    if formType == "CCD":
        rows = db(db.CCD.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc: IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
        table = SQLTABLE(rows,columns=["CCD.ccdNum",'CCD.file'],headers={"CCD.ccdNum":"CCD #","CCD.file":"CCD File"},upload="http://127.0.0.1:8000")
    
    elif formType == "RFI":
        rows = db(db.RFI.projectNum == str(request.vars.projectNum)).select()
        extracolumns = [{'label':'Reply to RFI',
                'class': '', #class name of the header
                'width':'', #width in pixels or %
                'content':lambda row, rc: A("Reply", _href=URL('default','replyRFI',args=row.id)) if auth.user.first_name == row.reqRefTo else A(" "),
                'selected': False #agregate class selected to this column
                }]
        table = SQLTABLE(rows,_width="800px",       
            columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.responseBy","RFI.responseDate","RFI.statusFlag"],headers=
            {"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To","RFI.responseDate":"Response Date","RFI.responseBy":"Need Response By","RFI.statusFlag":"Status Flag"}, extracolumns=extracolumns)
    
    elif formType == "Submittal":
        rows = db(db.Submittal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.submittal = str(URL('default','download',args=row.submittal))[1:]
        table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.statusFlag","Submittal.subType","Submittal.submittal"],
         headers={"Submittal.assignedTo":"Assigned To","Submittal.statusFlag":"Status Flag","Submittal.subType":"Type","Submittal.submittal":"Submitted File"},upload="http://127.0.0.1:8000")
    
    elif formType == "ProposalRequest":
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.statusFlag","ProposalRequest.sentTo","ProposalRequest.propDate"],
         headers={"ProposalRequest.reqNum":"Request Number","ProposalRequest.amendNum":"Amendment Number","ProposalRequest.sentTo":"Sent To","ProposalRequest.statusFlag":"Status Flag","ProposalRequest.propDate":"Proposal Request Date"})
    
    elif formType == "Proposal":
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["Proposal.propNum","Proposal.propReqRef","Proposal.propDate","Proposal.file"],
        headers={"Proposal.propNum":"Proposal Number","Proposal.propReqRef":"Proposal Request Reference Number","Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"},upload="http://127.0.0.1:8000")
    
    elif formType == "MeetingMinutes":
        rows = db().select(db.MeetingMinutes.ALL)
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["MeetingMinutes.meetDate","MeetingMinutes.file"],
        headers={"MeetingMinutes.meetDate":"Meeting Date","MeetingMinutes.file":"Submitted File"},upload="http://127.0.0.1:8000")
    
    elif formType == "Photo":    
        rows = db(db.Photos.projectNum == str(request.vars.projectNum)).select()
        db.Photos.flickrURL.represent=lambda flickrURL: A("View Photo", _href=flickrURL, _target="_blank")
        table = SQLTABLE(rows, columns=["Photos.title","Photos.description","Photos.flickrURL"], headers={"Photos.title":"Title", "Photos.description":"Description","Photos.flickrURL":"Photo"})

    if len(rows)==0:
        table = "There are no documents uploaded for this project section as of yet."
        fullTable = False

    return dict(formType=formType,
                myProfileForm=myProfileForm,
                projects=projects,
                table= table,
                image=image,
                footer=footer,
                header=header,
                css=css,
                fullTable=fullTable)

def replyRFI():
    id = request.args(0)
    db.RFI.statusFlag.requires = IS_IN_SET(['Outstanding','Closed'])
    replyRfiForm = SQLFORM(db.RFI, id, showid=False, labels={'rfiNum':'RFI #','projectNum':"Project #", 'requestBy':'Request by', 'dateSent':'Date Sent', 'reqRefTo':'Request Referred to', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':'Contractor\'s Suggestion', 'responseBy':'Need Response By', 'reply':'Reply', 'responseDate':'Response Date', 'statusFlag':'Status Flag'}, fields = ['rfiNum','projectNum','requestBy', 'dateSent', 'reqRefTo', 'drawingNum', 'detailNum', 'specSection', 'sheetName', 'grids', 'sectionPage', 'description', 'suggestion', 'responseBy', 'reply', 'responseDate', 'statusFlag'], _id="replyForm")
    
    if replyRfiForm != None:
        if replyRfiForm.process().accepted:
            row = db(db.RFI.id==id).select().first()
            row.update_record(reply=str(replyRfiForm.vars.reply), responseDate=str(replyRfiForm.vars.responseDate))       
            db.commit()   
            session.flash = T('RFI Reply Accepted')  
            redirect(URL('default', 'formtable', vars=dict(formType='RFI', projectNum=str(replyRfiForm.vars.projectNum))))                      
        elif replyRfiForm.errors:
            response.flash = 'form has errors'
        else:
            response.flash = 'please fill out the form'
            
    return dict(replyRfiForm = replyRfiForm, css=css, header=header, footer=footer)
    
def getOtherRoles(id):
    if auth.has_membership(user_id=id, role="Admin"):
        return "General"
    else:
        return "Admin"
        
def getUserRole(id):
    if auth.has_membership(user_id=id, role="Admin"):
        return "Admin"
    else:
        return "General"
