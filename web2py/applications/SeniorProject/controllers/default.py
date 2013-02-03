# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

ccdForm = SQLFORM(db.CCD, labels={'ccdNum':'CCD #','projectNum': "Project #"})

rfiForm = SQLFORM(db.RFI, labels={'rfiNum':'RFI #','projectNum':"Project #", 'requestBy':'Request by', 'dateSent':'Date Sent', 'reqRefTo':'Request Referred to', 'dateRec':'Date Received', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':'Contractor\'s Suggestion', 'reply':'Reply', 'responseBy':'Response by', 'responseDate':'Response Date'}, fields=['rfiNum','projectNum','requestBy', 'dateSent', 'reqRefTo', 'dateRec', 'drawingNum', 'detailNum', 'specSection', 'sheetName', 'grids', 'sectionPage', 'description', 'suggestion', 'reply', 'responseBy', 'responseDate'])

submittalForm = SQLFORM(db.Submittal, labels={'statusFlag':'Status Flag', 'projectNum':'Project Number', 'assignedTo':'Assigned to'})

proposalRequestForm = SQLFORM(db.ProposalRequest, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'})

proposalForm = SQLFORM(db.Proposal, labels={'reqNum':'Request #', 'projectNum':'Project Number', 'propDate':'Proposal Date'})

meetingMinutesForm = SQLFORM(db.MeetingMinutes, labels={'meetDate':'Meeting Date'})


projects = db(db.Project).select()

header = DIV(A(IMG(_src=URL('static','images/stock.jpeg')), _href=URL('default','index')), _id="header")
footer = DIV("This website brought to you by the Supreme Leader, Minion #3 (Alysse), Minion #2 (Scott), and the Sick One (Erik)", _id="footer")

auth.requires_login()
def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    
    if ccdForm.process().accepted:
        response.flash = 'form accepted'
    elif ccdForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if rfiForm.process().accepted:
        response.flash = 'form accepted'
    elif rfiForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if submittalForm.process().accepted:
        response.flash = 'form accepted'
    elif submittalForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if proposalRequestForm.process().accepted:
        response.flash = 'form accepted'
    elif proposalRequestForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if proposalForm.process().accepted:
        response.flash = 'form accepted'
    elif proposalForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
    
    if meetingMinutesForm.process().accepted:
        response.flash = 'form accepted'
    elif meetingMinutesForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
    
    return dict(ccdForm=ccdForm,
                projects=projects,
                rfiForm=rfiForm,
                submittalForm=submittalForm,
                proposalRequestForm=proposalRequestForm,
                proposalForm=proposalForm,
                meetingMinutesForm=meetingMinutesForm,
                header=header,
                footer=footer)

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

def register():
    admin_auth = session.auth
    auth.is_logged_in = lambda: False
    def post_register(form):
        session.auth = admin_auth
        auth.user = session.auth.user
    auth.settings.register_onaccept = post_register
    return dict(form=auth.register())

def deleteusers():
     rows=db(db.auth_user.id>0).select() 
     db.auth_user.id.represent=lambda id: DIV(id,INPUT (_type='checkbox',_name='check%i'%id)) 
     table=FORM(SQLTABLE(rows),INPUT(_type='submit')) 
     if table.accepts(request.vars): 
           pass # or so something not sure what you want to do 
     return dict(table=table, footer=footer, header=header)
     
def createproject():
    form = SQLFORM(db.Project, labels={'openDate':'Open Date', 'closedDate':'Closed Date', 'projNum':'Project Number'})
    if form.process().accepted:
       response.flash = 'form accepted'
    elif form.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'please fill out the form'
    return dict(form=form, footer=footer, header=header)
    
def manageprojects():
    table = None
    rows = db().select(db.Project.ALL)
    #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc:     IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
    table = SQLTABLE(rows,columns=["Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #", "Project.archived":"Archived"})
    return dict(table=table, footer=footer, header=header)
    
def archiveprojects():
    table = None
    rows = db(db.Project.archived == True).select()
    #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc:     IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
    table = SQLTABLE(rows,columns=["Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #", "Project.archived":"Archived"})
    return dict(table=table, footer=footer, header=header)
    
def manageusers():
    table = None
    #rows = db().select(db.Users.ALL)
    #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc:     IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
    #table = SQLTABLE(rows,columns=["Project.name","Project.projNum",'Project.openDate',"Project.closedDate"],headers={"Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #", "Project.archived":"Archived"})
    return dict(table=table, footer=footer, header=header)

def formtable():
    formType = request.vars.formType
    if ccdForm.process().accepted:
        response.flash = 'form accepted'
    elif ccdForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if rfiForm.process().accepted:
        response.flash = 'form accepted'
    elif rfiForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if submittalForm.process().accepted:
        response.flash = 'form accepted'
    elif submittalForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if proposalRequestForm.process().accepted:
        response.flash = 'form accepted'
    elif proposalRequestForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
        
    if proposalForm.process().accepted:
        response.flash = 'form accepted'
    elif proposalForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
    
    if meetingMinutesForm.process().accepted:
        response.flash = 'form accepted'
    elif meetingMinutesForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
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
            columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.dateRec","RFI.responseBy","RFI.responseDate","RFI.statusFlag"],headers=
            {"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To","RFI.dateRec":"Date Received","RFI.responseDate":"Response Date","RFI.responseBy":"Response By","RFI.statusFlag":"Status Flag"})
    elif formType == "Submittal":
        rows = db(db.Submittal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.submittal = str(URL('default','download',args=row.submittal))[1:]
        table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.statusFlag","Submittal.submittal"],
         headers={"Submittal.assignedTo":"Assigned To","Submittal.statusFlag":"Status Flag","Submittal.submittal":"Submitted File"},upload="http://127.0.0.1:8000")
    elif formType == "ProposalRequest":
        rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select()
        table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.sentTo","ProposalRequest.propDate"],
         headers={"ProposalRequest.reqNum":"Request Number","ProposalRequest.amendNum":"Amendment Number","ProposalRequest.sentTo":"Sent To","ProposalRequest.propDate":"Proposal Request Date"})
    elif formType == "Proposal":
        rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["Proposal.reqNum","Proposal.propDate","Proposal.file"],
        headers={"Proposal.reqNum":"Proposal Number","Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"},upload="http://127.0.0.1:8000")
    elif formType == "MeetingMinutes":
        rows = db().select(db.MeetingMinutes.ALL)
        for row in rows:
            row.file = str(URL('default','download',args=row.file))[1:]
        table = SQLTABLE(rows, columns=["MeetingMinutes.meetDate","MeetingMinutes.file"],
        headers={"MeetingMinutes.meetDate":"Meeting Date","MeetingMinutes.file":"Submitted File"},upload="http://127.0.0.1:8000")

    if len(rows)==0:
        table = "There are no documents uploaded for this project section as of yet."
        fullTable = False

    return dict(formType=formType,
                ccdForm=ccdForm,                
                rfiForm=rfiForm,
                submittalForm=submittalForm,
                proposalRequestForm=proposalRequestForm,
                proposalForm=proposalForm,
                meetingMinutesForm=meetingMinutesForm,
                projects=projects,
                table= table,
                image=image,
                footer=footer,
                header=header,
                fullTable=fullTable)
