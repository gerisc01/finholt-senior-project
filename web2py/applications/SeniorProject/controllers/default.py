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

rfiForm = SQLFORM(db.RFI, labels={'rfiNum':'RFI #', 'requestBy':'Request by', 'dateSent':'Date sent', 'reqRefTo':'Request referred to', 'dateRec':'Date received', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':'Contractor\'s suggestion', 'reply':'Reply', 'responseBy':'Response by', 'responseDate':'Response date'})

submittalForm = SQLFORM(db.Submittal, labels={'statusFlag':'Status flag', 'assignedTo':'Assigned to'})

proposalRequestForm = SQLFORM(db.ProposalRequest, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'})

proposalForm = SQLFORM(db.Proposal, labels={'reqNum':'Request #', 'propDate':'Proposal Date'})

meetingMinutesForm = SQLFORM(db.MeetingMinutes, labels={'meetDate':'Meeting Date'})


projects = db(db.Project).select()

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
    
    return dict(ccdForm=ccdForm,projects=projects)

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

def createproject():
    form = SQLFORM(db.Project)
    if form.process().accepted:
       response.flash = 'form accepted'
    elif form.errors:
       response.flash = 'form has errors'
    else:
       response.flash = 'please fill out the form'
    return dict(form=form)

def formtable():
    formType = request.vars.formType
    if ccdForm.process().accepted:
        response.flash = 'form accepted'
    elif ccdForm.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'    
    table = None
    image = None
    if formType == "CCD":
        rows = db(db.CCD.projectNum == str(request.vars.projectNum)).select()
        myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 'content': lambda row, rc: IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
        table = SQLTABLE(rows,columns=["CCD.ccdNum",'CCD.file'],headers={"CCD.ccdNum":"CCD #","CCD.file":"CCD File"},extracolumns=myextracolumns)
    return dict(formType=formType,
                ccdForm=ccdForm,
                projects=projects,
                table= table,
                image=image)
