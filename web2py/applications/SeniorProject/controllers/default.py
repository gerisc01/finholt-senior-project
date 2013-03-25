# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

import flickrapi


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

projects = None





header = DIV(A(IMG(_src=URL('static','images/bluebannertext.jpg')), _href=URL('default','index')), _id="header")
header_archived = DIV(A(IMG(_src=URL('static','images/bluebannertext.jpg'))), _id="header")
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
    user = db(db.auth_user.id ==auth.user.id).select().first()
    projects = []
    for item in user.projects:
        rows = db((db.Project.archived == False) & (db.Project.id == item)).select()
        if len(projects) ==0:
            projects = rows
        else:
            projects= projects & rows
    

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
    if form.process().accepted:
       response.flash = str(request.vars.first_name) + ' created as user'
    elif form.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'Please create a user'
    if form.validate():
        admin_user = auth.user
        auth.get_or_create_user(form.vars)
        auth.add_membership(auth.id_group(role="General"),auth.user_id)
        auth.user = admin_user
        redirect(URL('default','register'))
    return dict(form=form, header=header, footer=footer, css=css)


@auth.requires_login()
@auth.requires_membership('Admin')
def changepermissions():
     rows=db(db.auth_user.id>0).select() 
     db.auth_user.id.represent=lambda id: SELECT(getUserRole(id), XML(getOtherRoles(id)), _name='%i'%id)
     table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Change Permission","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit'))
 
     if table.accepts(request.vars): 
        for item in request.vars.keys():
            if item.isdigit():
                if not auth.has_membership(user_id=int(item), role=request.vars[item]):
                    if auth.has_membership(user_id=int(item), role=getUserRole(int(item))): #in case they are in their individual user group. We should only delete them from the group we are in if they are switching from General to Admin or vice versa.
                        
                        auth.del_membership(auth.id_group(role=getUserRole(int(item))),int(item))
                    auth.add_membership(auth.id_group(role=request.vars[item]),int(item))
        session.flash = 'Permissions changed'
        redirect(URL('default','changepermissions'))
     elif table.errors:
         session.flash = 'An error has occured'
     else:
         session.flash = 'Modify user permissions'
     
     return dict(table=table, footer=footer, header=header, css=css)

@auth.requires_membership("Admin")
@auth.requires_login()
def addtoproject():
    rows=db(db.auth_user.id>0).select() 
    db.auth_user.id.represent=lambda id: DIV('', XML(getAllProjectsHtml(id)), _name='%i'%id)
    table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Add To","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit')) 
    if table.accepts(request.vars):
        for userid in request.vars.keys():
            if userid.isdigit():
                projectList = []
                for item in request.vars[userid]:
                    projectList.append(int(item))
                db(db.auth_user.id ==int(userid)).update(projects=projectList)
    return dict(table=table, footer=footer, header=header, css=css)

@auth.requires_membership("Admin")
@auth.requires_login()
def deletefromproject():
    rows=db(db.auth_user.id>0).select() 
    db.auth_user.id.represent=lambda id: DIV('', XML(getUsersProjectsHtml(id)), _name='%i'%id)
    table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Remove From","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit')) 
    if table.accepts(request.vars): 
        for userid in request.vars.keys():
            if userid.isdigit():
                user = db(db.auth_user.id ==int(userid)).select().first()
                projects = user.projects
                for item in request.vars[userid]:
                    projects.remove(int(item))

                db(db.auth_user.id ==int(userid)).update(projects=projects)

    return dict(table=table, footer=footer, header=header, css=css)

@auth.requires_login()
@auth.requires_membership('Admin')
def deleteusers():
     rows=db(db.auth_user.id>0).select() 
     db.auth_user.id.represent=lambda id: DIV(id,INPUT (_type='checkbox',_name='%i'%id)) 
     table=FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.first_name','auth_user.last_name','auth_user.email'], headers={"auth_user.id":"Remove User","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit'))
     if table.process().accepted:
       response.flash = str(request.vars.first_name) + ' deleted as user'
     elif table.errors:
       response.flash = 'form has errors'
     else:
       response.flash = 'Select users to delete'
     if table.accepts(request.vars): 
        for item in request.vars.keys():
            if item.isdigit():
                db(db.auth_user.id == int(item)).delete()
        session.flash = 'User deleted'
        redirect(URL('default','deleteusers'))

     return dict(table=table, footer=footer, header=header,css=css)
 
@auth.requires_login()    
@auth.requires_membership('Admin')
def createproject():
    form = SQLFORM(db.Project, labels={'openDate':'Open Date', 'closedDate':'Closed Date', 'projNum':'Project Number'})
    if form.process().accepted:
       response.flash = str(request.vars.name) + ' has been created'
    elif form.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'please create a project'
    return dict(form=form, footer=footer, header=header, css=css)

@auth.requires_login()   
@auth.requires_membership('Admin')
def manageprojects():
    table = None
    rows = db(db.Project.archived == False).select()    
    db.Project.id.represent=lambda id: DIV(id,INPUT (_type='checkbox',_name='%i'%id)) 
    table = FORM(SQLTABLE(rows,columns=["Project.id","Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.id":"Archive","Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #"}),INPUT(_type='submit'))
    if table.process().accepted:
       response.flash = str(request.vars.name) + ' has been archived'
    elif table.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'Select a project to archive'
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
    extracolumns = [{'label':'View Archived Project',
                'class': '', #class name of the header
                'width':'', #width in pixels or %
                'content':lambda row, rc: A("View", _href=URL('default','viewArchive', args=row.id), _target='new'),
                'selected': False #agregate class selected to this column
                }]
    table = SQLTABLE(rows,columns=["Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #", "Project.archived":"Archived"},extracolumns=extracolumns)
    return dict(table=table, footer=footer, header=header, css=css)
    
def viewArchive():
    project = db(db.Project.id == request.args(0)).select().first()
    return dict(project=project, header=header_archived, css=css)
    
def newsfeed():
    entries = db().select(db.NewsFeed.ALL)  
    return dict(entries=entries, fullTable=True, projects=projects, myProfileForm=myProfileForm, header=header, footer=footer, css=css)
    
def newsfeedarchived():
    project = db(db.Project.projNum == request.vars.projectNum).select().first()
    entries = db().select(db.NewsFeed.ALL)   
    return dict(entries=entries, fullTable=True, project=project, header=header_archived, css=css)  

def showform():
    user = db(db.auth_user.id ==auth.user.id).select().first()
    projects = []
    for item in user.projects:
        rows = db((db.Project.archived == False) & (db.Project.id == item)).select()
        if len(projects) ==0:
            projects = rows
        else:
            projects= projects & rows
    displayForm = request.vars.displayForm
    form = None
    if displayForm == "CCD":
        form = SQLFORM(db.CCD, labels={'ccdNum':'CCD #','projectNum': "Project #"})
        rows = db(db.CCD.projectNum == str(request.vars.projectNum)).select()
        form.vars.ccdNum = len(rows) + 1
        form.vars.projectNum = request.vars.projectNum
    elif displayForm == "RFI":
        db.RFI.reqRefTo.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s'+' '+'%(last_name)s')
        form = SQLFORM(db.RFI, labels={'rfiNum':'RFI #','projectNum':"Project #", 'projectName':'Project Name', 'owner':'Owner', 'requestBy':'Request by', 'dateSent':'Date Sent', 'reqRefTo':'Request Referred to', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':'Contractor\'s Suggestion', 'responseBy':'Need Response By'}, fields=['rfiNum','projectNum','projectName','owner','requestBy', 'dateSent', 'reqRefTo', 'drawingNum', 'detailNum', 'sheetName', 'grids', 'specSection', 'sectionPage', 'description', 'suggestion', 'responseBy'])
        rows = db(db.RFI.projectNum == str(request.vars.projectNum)).select()
        form.vars.rfiNum = len(rows) + 1
        form.vars.requestBy = auth.user.first_name
        form.vars.statusFlag = "Outstanding"  
        form.vars.projectNum = request.vars.projectNum          
    elif displayForm == "Submittal":
        db.Submittal.subType.requires = IS_IN_SET(['Samples','Shop Drawing','Product Data'])
        db.Submittal.assignedTo.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s'+' '+'%(last_name)s')
        db.Submittal.statusFlag.requires = IS_IN_SET(['Approved','Resubmit','Approved with Comments','Submitted for Review'])
        form = SQLFORM(db.Submittal, labels={'statusFlag':'Status Flag', 'projectNum':'Project Number', 'subType':'Submittal Type', 'sectNum':'Section Number','assignedTo':'Assigned to'}) 
        form.vars.projectNum = request.vars.projectNum
    elif displayForm == "ProposalRequest":     
        form = SQLFORM(db.ProposalRequest, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'}, fields =['reqNum','amendNum','projectNum','subject','propDate','sentTo','cc','description'])
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        form.vars.statusFlag = "Open"
        form.vars.reqNum = len(rows) + 1
        form.vars.creator = auth.user.id
        form.vars.projectNum = request.vars.projectNum
    elif displayForm == "Proposal":
        therows = len(db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select(db.ProposalRequest.reqNum))
        mylist = list(range(1,therows+1))
        db.Proposal.propReqRef.requires = IS_IN_SET(mylist)
        form = SQLFORM(db.Proposal, labels={'propNum':'Proposal #', 'propReqRef':'Proposal Request Reference #', 'projectNum':'Project Number', 'propDate':'Proposal Date'})
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        form.vars.propNum = len(rows) + 1
        form.vars.projectNum = request.vars.projectNum
    elif displayForm == "MeetingMinutes":
        form = SQLFORM(db.MeetingMinutes, labels={'projectNum':'Project Number','meetDate':'Meeting Date'})
        form.vars.projectNum = request.vars.projectNum
    elif displayForm == "Photo":                         
        form = SQLFORM(db.Photos, labels={'projectNum':'Project Number', 'title':'Title', 'description':'Description', 'photo':'Photo'}, fields = ['projectNum','title','description','photo'])
        form.vars.projectNum = request.vars.projectNum
    if form != None:
        if form.process().accepted:
            response.flash = T('form accepted')
            if displayForm == "Photo":    #If the form submitted is a photo form, we need to upload it to flickr and delete the photo from our database
                 uploadPhotoToFlickr(form)
            elif displayForm == "RFI":    #If the form submitted is an RFI form, we need to put the name of person the RFI is referred to instead of the id
                reqUser = db(db.auth_user.id == form.vars.reqRefTo).select().first()
                row = db(db.RFI.id == form.vars.id).select().first()
                row.update_record(reqRefTo = reqUser.first_name + " " + reqUser.last_name)
            elif displayForm == "Submittal": #If the form submitted is a Submittal, we need to put the name of person it is assigned to instead of the id
                assignTo = db(db.auth_user.id == form.vars.assignedTo).select().first()
                row = db(db.Submittal.id == form.vars.id).select().first()
                row.update_record(assignedTo= assignTo.first_name + " " + assignTo.last_name)
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
def formtablearchived():
    formType = request.vars.formType
    project =  db(db.Project.projNum == request.vars.projectNum).select().first()
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
        table = SQLTABLE(rows,_width="800px",       
            columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.responseDate"],headers=
            {"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To","RFI.responseDate":"Response Date"})
    
    elif formType == "Submittal":
        rows = db(db.Submittal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.submittal = str(URL('default','download',args=row.submittal))[1:]
        table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.subType","Submittal.sectNum","Submittal.submittal"],
         headers={"Submittal.assignedTo":"Assigned To","Submittal.subType":"Type","Submittal.sectNum":"Section Number","Submittal.submittal":"Submitted File"},upload="http://127.0.0.1:8000")
    
    elif formType == "ProposalRequest":
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.sentTo","ProposalRequest.propDate"],
         headers={"ProposalRequest.reqNum":"Request Number","ProposalRequest.amendNum":"Amendment Number","ProposalRequest.sentTo":"Sent To","ProposalRequest.propDate":"Proposal Request Date"})
    
    elif formType == "Proposal":
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["Proposal.propNum","Proposal.propReqRef","Proposal.propDate","Proposal.file"],
        headers={"Proposal.propNum":"Proposal Number","Proposal.propReqRef":"Proposal Request Reference Number","Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"},upload="http://127.0.0.1:8000")
    
    elif formType == "MeetingMinutes":
        rows = db(db.MeetingMinutes.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["MeetingMinutes.meetDate","MeetingMinutes.file"],
        headers={"MeetingMinutes.meetDate":"Meeting Date","MeetingMinutes.file":"Submitted File"},upload="http://127.0.0.1:8000")
    
    elif formType == "Photo":    
        rows = db(db.Photos.projectNum == str(request.vars.projectNum)).select()
        db.Photos.flickrURL.represent=lambda flickrURL: A("View Photo", _href=flickrURL, _target="_blank")
        table = SQLTABLE(rows, columns=["Photos.title","Photos.description","Photos.flickrURL"], headers={"Photos.title":"Title", "Photos.description":"Description","Photos.flickrURL":"Photo"})

    if len(rows)==0:
        table = "There were no documents uploaded for this project section."
        fullTable = False

    return dict(formType=formType,
                project=project,
                table= table,
                header=header_archived,
                css=css,
                fullTable=fullTable)

@auth.requires_login()
def formtable():
    user = db(db.auth_user.id ==auth.user.id).select().first()
    projects = []
    for item in user.projects:
        rows = db((db.Project.archived == False) & (db.Project.id == item)).select()
        if len(projects) ==0:
            projects = rows
        else:
            projects= projects & rows

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
                'content':lambda row, rc: A("Reply", _href=URL('default','replyRFI',args=row.id)) if auth.user.first_name +" " + auth.user.last_name == row.reqRefTo else A(" "),
                'selected': False #agregate class selected to this column
                }]
        table = SQLTABLE(rows,_width="800px",       
            columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.responseBy","RFI.responseDate","RFI.statusFlag"],headers=
            {"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To","RFI.responseDate":"Response Date","RFI.responseBy":"Need Response By","RFI.statusFlag":"Status Flag"}, extracolumns=extracolumns)
    
    elif formType == "Submittal":
        rows = db(db.Submittal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.submittal = str(URL('default','download',args=row.submittal))[1:]
        table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.statusFlag","Submittal.subType","Submittal.sectNum","Submittal.submittal"],
         headers={"Submittal.assignedTo":"Assigned To","Submittal.statusFlag":"Status Flag","Submittal.subType":"Type","Submittal.sectNum":"Section Number","Submittal.submittal":"Submitted File"},upload="http://127.0.0.1:8000")
    
    elif formType == "ProposalRequest":
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        extracolumns = [{'label':'Change Status',
                'class': '', #class name of the header
                'width':'', #width in pixels or %
                'content':lambda row, rc: A("Make Change", _href=URL('default','changePropReq',args=row.id)) if auth.user.id == row.creator else A(" "),
                'selected': False #agregate class selected to this column
                }]
        table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.statusFlag","ProposalRequest.sentTo","ProposalRequest.propDate"],
         headers={"ProposalRequest.reqNum":"Request Number","ProposalRequest.amendNum":"Amendment Number","ProposalRequest.sentTo":"Sent To","ProposalRequest.statusFlag":"Status Flag","ProposalRequest.propDate":"Proposal Request Date"},extracolumns=extracolumns)
    
    elif formType == "Proposal":
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["Proposal.propNum","Proposal.propReqRef","Proposal.propDate","Proposal.file"],
        headers={"Proposal.propNum":"Proposal Number","Proposal.propReqRef":"Proposal Request Reference Number","Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"},upload="http://127.0.0.1:8000")
    
    elif formType == "MeetingMinutes":
        rows = db(db.MeetingMinutes.projectNum == str(request.vars.projectNum)).select()
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
            
    return dict(replyRfiForm=replyRfiForm, css=css, header=header, footer=footer)

def changePropReq():
    id = request.args(0)
    db.ProposalRequest.statusFlag.requires = IS_IN_SET(['Open','Closed'])     
    changePropReqForm = SQLFORM(db.ProposalRequest, id, showid=False, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'statusFlag':'Status', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'}, fields =['reqNum','amendNum','projectNum','subject','propDate','sentTo','cc','description','statusFlag'], _id="changePropReqForm")
        
    if changePropReqForm != None:
        if changePropReqForm.process().accepted:
            row = db(db.ProposalRequest.id==id).select().first()
            row.update_record(statusFlag=str(changePropReqForm.vars.statusFlag))       
            db.commit()   
            session.flash = T('Status Change Accepted')  
            redirect(URL('default', 'formtable', vars=dict(formType='ProposalRequest', projectNum=str(changePropReqForm.vars.projectNum))))                      
        elif changePropReqForm.errors:
            response.flash = 'form has errors'
        else:
            response.flash = 'please fill out the form'
            
    return dict(changePropReqForm=changePropReqForm, css=css, header=header, footer=footer)  

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

def getAllProjectsHtml(id):
    html=''
    projects = db(db.Project.archived == False).select()
    user = db(db.auth_user.id == id).select().first()

    for row in projects:
        if user.projects != None:
            if row.id not in user.projects:
                html +=  '<input value="'+str(row.id)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(row.id)+"</br>"
        else:
            html +=  '<input value="'+str(row.id)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(row.id)+"</br>"
    if html =='':
        html = "<p>In all projects</p>"
    return html 

def getUsersProjectsHtml(id):
    html = ''

    
    user = db(db.auth_user.id == id).select().first()
    if user.projects != None and len(user.projects)>=1:
        for projId in user.projects:
            project = db((db.Project.archived == False) & (db.Project.id == projId)).select().first()
            html +=  '<input value="'+str(project.id)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(project.id)+"</br>"
    else:
        html = "<p>Not on any projects</p>"
    return html
