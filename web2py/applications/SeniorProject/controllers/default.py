# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

#Import necessary modules
import flickrapi
import appy
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
import mechanize
import cookielib
import urllib
import urllib2
import json

#Flickr API keys
KEY = '614fd86a34a00d38293c7e803d14c3ab'
SECRET_KEY = 'ad86826c3187eb4d'
USER_ID = '93142072@N05'

#Create the static links to be passed in to the views
header = DIV(A(IMG(_src=URL('static','images/bluebannertext.jpg')), _href=URL('default','index')), _id="header")
header_archived = DIV(A(IMG(_src=URL('static','images/bluebannertext.jpg'))), _id="header")
footer = DIV(A("Home Page", _href=URL('default','index')), TD("------"), A("Log out", _href=URL('default','user', args='logout')), _id="footer")
css = "/SeniorProject/static/css/bluestyle.css"

#Returns the current user (object) of the site
def getUser():
    user = None
    if auth.user != None:
        user = db(db.auth_user.id == auth.user.id).select().first()
    return user

#Returns the form that will be displayed when the "My Profile" tab is clicked (the parameter passed in is a user object)
def getProfileFormForUser(user):
    if user != None:        #We will display the form with the user's current information filled in
        record = user.id    #Gets the info for the current user    
        myProfileForm = SQLFORM(db.auth_user, record, showid=False, labels={'first_name':'First Name', 'last_name':'Last Name', 'email':'E-mail', 'phone':'Phone Number', 'password':'New Password'}, fields = ['first_name','last_name','email','phone'],_id="profileForm")
    else:                   #Display the form with no fields filled in 
        myProfileForm = SQLFORM(db.auth_user, showid=False, labels={'first_name':'First Name', 'last_name':'Last Name', 'email':'E-mail', 'phone':'Phone Number', 'password':'New Password'}, fields = ['first_name','last_name','email','phone'],_id="profileForm")
    return myProfileForm

#Returns all the non-archived projects the specified user is associated with (the parameter passed in is a user object)
def getProjectsForUser(user):
    projects = []
    if user != None and user.projects != None:
        if auth.has_membership(user_id=user.id, role="Admin"):    #If the user is an admin, get all the non-archived projects
            projects = db(db.Project.archived == False).select()
        else:
            for projNum in user.projects:
                rows = db((db.Project.archived == False) & (db.Project.projNum == projNum)).select()
                if len(projects) == 0:
                    projects = rows
                else:
                    projects= projects & rows   
    return projects

#Checks if the current token is valid; if not, then redirects to flickr to be authenticated and get a token
def setUpFlickrStuff():   
    if not db(db.PhotoToken).isempty():                                #We already have a PhotoToken, so use the token when creating a flickr object
        tok = (db.PhotoToken(db.PhotoToken.id > 0)).token              #Get the token from the database
        flickr = flickrapi.FlickrAPI(KEY, SECRET_KEY, token = tok)     #Create a flickr object
    else:
        flickr = flickrapi.FlickrAPI(KEY, SECRET_KEY)
    
    if not db(db.PhotoToken).isempty():
        #We have a token, but it might not be valid
        #Check the token. If there was an error, then delete the token from the database
        try:
            flickr.auth_checkToken() 
        except flickrapi.FlickrError:
            db(db.PhotoToken.id > 0).delete()
    if db(db.PhotoToken).isempty():                 #We don't have the token yet, or it was deleted because it wasn't valid
        if request.vars.frob:                       #If the frob is in the request (coming back from being authenticated by flickr)
            db.PhotoToken[0] = {"token" : flickr.get_token(request.vars.frob)}    #Insert a new row into the database with the new token
        else:
            url = flickr.web_login_url('write')     #Get the url to go to in order to authenticate
            br = mechanize.Browser()
            # Browser options
            br.set_handle_equiv(True)
            br.set_handle_gzip(True)
            br.set_handle_redirect(True)
            br.set_handle_referer(True)
            br.set_handle_robots(False)

            # Cookie Jar
            cj = cookielib.LWPCookieJar()
            br.set_cookiejar(cj)

            # Follows refresh 0 but not hangs on refresh > 0
            br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
            r = br.open(url)
            br.select_form("login_form")
            br.form["login"]="alyssealyssetest"
            br.form["passwd"]="finholt1"
            br.find_control(".persistent").items[0].selected=True
            br.submit()                                 #Redirect to that website
    return flickr
            
            
#Do all the set-up/initializing that is necessary for using the site (calling the above functions)   
user = getUser()                            #Get the current user of the site
projects = getProjectsForUser(user)         #Get the projects that the user is associated with
myProfileForm = getProfileFormForUser(user) #Get the form for the "My Profile" tab
flickr = setUpFlickrStuff()                 #Make sure all the flickr stuff is good to go (make sure we're authenticated)


#Called when a new photoForm is submitted (called from showform when the photoForm is accepted)
def uploadPhotoToFlickr(photoForm):
    try:
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
    
        #Delete the corresponding row in our database (because we don't want to store the actual photo no our server)
        db(db.Photos.id == photoWeb2pyId).delete()        
        
        #Create a new row in our database with all the same info as the deleted row, but without the photo file
        db.Photos.insert(projectNum=projNum, flickrURL=flickrUrl, title=title, description=descr)
        response.flash = "Upload success"
    except:
        db(db.Photos.id == photoWeb2pyId).delete()
        response.flash = "Upload failed"
 

#Returns a dictionary used by the view default/index.html (which is the home screen)
@auth.requires_login()
def index():
    response.flash = "Welcome " + auth.user.first_name + "!"    #Welcome the user to the site
    #response.flash = "Erik Smellz"
    projectNums = []                                            #Get the project numbers of all the projects the user is associated with
    for project in projects:
        projectNums.append(project.projNum) 
    
    #Get all the newsfeed entries for the user's projects, ordering by time created (most recent entry listed first)
    entries = db(db.NewsFeed.projectNum.belongs(projectNums)).select(orderby=~db.NewsFeed.created_on)
    
    if entries == None or len(entries) == 0:                    #If there aren't any entries, set entries to None (this is checked in the View)
        entries = None
    elif len(entries) > 20:
        entries = entries[0:20]                                 #Only display the first 20 newsfeed entries on the homescreen
        
    if myProfileForm.process().accepted:
       response.flash = "Profile updated successfully!"
    elif myProfileForm.errors:
       response.flash = 'Form has errors'
    
    return dict(projects=projects,
                myProfileForm=myProfileForm,
                header=header,
                footer=footer,
                css=css,
                entries=entries)

#Created by web2py
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

#Created by web2py
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)

#Created by web2py
def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

#Created by web2py
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

#This is called when an admin clicks "Create User". It returns a dictionary used by the view default/regiser.html
@auth.requires_login()
@auth.requires_membership('Admin')
def register():
    form = SQLFORM(db.auth_user)                                            #Create a form with the fields for a user
   
    if form.validate():                                                     #Add the new user with membership in the General group (rather than Admin)
        admin_user = auth.user
        auth.get_or_create_user(form.vars)
        db(db.auth_membership.user_id == auth.user_id).delete()
        auth.add_membership(auth.id_group(role="General"),auth.user_id)
        auth.user = admin_user
        response.flash = str(request.vars.first_name) + ' created as user'
    elif form.errors:
       response.flash = 'Form has errors'
    else:
       response.flash = 'Please create a user'         
        
    return dict(form=form, header=header, footer=footer, css=css)

#This is called when an admin clicks "User Permissions". It returns a dictionary used by the view default/changepermissions.html
@auth.requires_login()
@auth.requires_membership('Admin')
def changepermissions():
     #Get all the users in alphabetical order, except the current user (don't want a user to change his own permissions)
     rows = db(db.auth_user.id != auth.user.id).select(orderby=db.auth_user.last_name)     
     #Represent the user's id as a dropdown with the values of Admin or General, with the current value as the user's current group membership
     db.auth_user.id.represent = lambda id: SELECT(getUserRole(id), XML(getOtherRoles(id)), _name='%i'%id) 
     #Create a table with all the users and their current memberships
     table = FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.last_name','auth_user.first_name','auth_user.email'], headers={"auth_user.id":"Change Permission","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}),INPUT(_type='submit'))
 
     if table.accepts(request.vars): 
        for item in request.vars.keys():               #For each user selected..
            if item.isdigit():
                if not auth.has_membership(user_id=int(item), role=request.vars[item]):
                    if auth.has_membership(user_id=int(item), role=getUserRole(int(item))): #in case they are in their individual user group. We should only delete them from the group we are in if they are switching from General to Admin or vice versa.
                        auth.del_membership(auth.id_group(role=getUserRole(int(item))),int(item))
                    auth.add_membership(auth.id_group(role=request.vars[item]),int(item)) #Add the user's membership
                    
        session.flash = 'Permissions changed'
        redirect(URL('default','changepermissions'))    #Redirect to the same screen so the admin can see the current permission level of every user
        
     elif table.errors:
         session.flash = 'An error has occured'
     else:
         session.flash = 'Modify user permissions'
     
     return dict(table=table, footer=footer, header=header, css=css)

#This is called when an admin clicks "Add Users to Projects". It returns a dictionary used by the view default/addtoproject.html
@auth.requires_membership("Admin")
@auth.requires_login()
def addtoproject():
    rows = db(db.auth_user.id > 0).select(orderby=db.auth_user.last_name)        #Get all the users of the site (in alphabetical order)
    #Represent the user's id as checkboxes of possible projects for the user to be added to
    db.auth_user.id.represent = lambda id: DIV('', XML(getAllProjectsHtml(id)), _name='%i'%id) 
    #Create a table of the information
    table = FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.last_name','auth_user.first_name','auth_user.email','auth_user.role'], headers={"auth_user.id":"Add To","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email","auth_user.role":"Role"}), INPUT(_type='submit')) 
    
    if table.accepts(request.vars):
        for userid in request.vars.keys():               #For each user selected..
            if userid.isdigit():
                projectList = db(db.auth_user.id == int(userid)).select().first().projects
                if projectList == None:
                    projectList = []
                    
                if type(request.vars[userid]) is list:
                    for item in request.vars[userid]:
                        projectList.append(int(item))
                else:
                    projectList.append(int(request.vars[userid]))
                db(db.auth_user.id == int(userid)).update(projects=projectList)
        redirect(URL('default','addtoproject'))
    return dict(table=table, footer=footer, header=header, css=css)

#This is called when an admin clicks "Delete Users from Projects". It returns a dictionary used by the view default/deletefromproject.html
@auth.requires_membership("Admin")
@auth.requires_login()
def deletefromproject():
    rows = db(db.auth_user.id > 0).select(orderby=db.auth_user.last_name)    #Get all the users of the site (in alphabetical order)
    #Represents the user's id as checkboxes of all the user's associated projects
    db.auth_user.id.represent = lambda id: DIV('', XML(getUsersProjectsHtml(id)), _name='%i'%id) 
    #Create a table of the information
    table = FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.last_name','auth_user.first_name','auth_user.email','auth_user.role'], headers={"auth_user.id":"Remove From","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email","auth_user.role":"Role"}),INPUT(_type='submit')) 
   
    if table.accepts(request.vars): 
        for userid in request.vars.keys():                                    #For each user selected..
            if userid.isdigit():
                user = db(db.auth_user.id ==int(userid)).select().first()
                projects = user.projects
                
                if type(request.vars[userid]) is list:
                    for item in request.vars[userid]:
                        projects.remove(int(item))
                else:
                    projects.remove(int(request.vars[userid]))
                db(db.auth_user.id ==int(userid)).update(projects=projects)
        redirect(URL('default','deletefromproject'))
    return dict(table=table, footer=footer, header=header, css=css)

#This is called when an admin clicks "Delete User". It returns a dictionary used by the view default/deleteusers.html
@auth.requires_login()
@auth.requires_membership('Admin')
def deleteusers():
     #Get all the users on the site in alphabetical order, except the current user (don't want someone to delete himself)
     rows = db(db.auth_user.id != auth.user.id).select(orderby=db.auth_user.last_name)  
     db.auth_user.id.represent = lambda id: DIV(id, INPUT (_type='checkbox',_name='%i'%id)) #Create a checkbox for each user
     #Create a table of the information
     table = FORM(SQLTABLE(rows, columns=["auth_user.id",'auth_user.last_name','auth_user.first_name','auth_user.email'], headers={"auth_user.id":"Remove User","auth_user.first_name":"First Name","auth_user.last_name":"Last Name","auth_user.email":"Email"}), INPUT(_type='submit'))
     
     table["_onsubmit"] = "return confirm('Are you sure you want to delete this user?');"
     if table.process().accepted:
       response.flash = str(request.vars.first_name) + ' deleted as user'
     elif table.errors:
       response.flash = 'Form has errors'
     else:
       response.flash = 'Select users to delete'
     
     if table.accepts(request.vars): 
        for item in request.vars.keys():                     #For each user selected..
            if item.isdigit():
                db(db.auth_user.id == int(item)).delete()    #Delete the user that was selected
                
        session.flash = 'User deleted'
        redirect(URL('default','deleteusers'))               #Redirect back to the same screen

     return dict(table=table, footer=footer, header=header,css=css)

#This is called when an admin clicks "Add Project". It returns a dictionary used by the view default/createproject.html 
@auth.requires_login()    
@auth.requires_membership('Admin')
def createproject():
    #Create a form for inserting a new project into the database
    form = SQLFORM(db.Project, labels={'projNum':'Project Number', 'openDate':'Open Date', 'closedDate':'Closed Date'})
    
    if form.process().accepted:
       response.flash = str(request.vars.name) + ' has been created'
    elif form.errors:
       response.flash = 'Form has errors'
    else:
       response.flash = 'Please create a project'
       
    return dict(form=form, footer=footer, header=header, css=css)

#This is called when an admin clicks "Manage Projects". It returns a dictionary used by the view default/manageprojects.html
@auth.requires_login()   
@auth.requires_membership('Admin')
def manageprojects():
    table = None
    rows = db(db.Project.archived == False).select() #Get all the non-archived projects
    
    if len(rows) == 0:
        table = "There are currently no non-archived projects"
        
    else:   #There is at least one on-going project
        db.Project.id.represent = lambda id: DIV(INPUT(_type='checkbox',_name='%i'%id)) #Represent the project id as a checkbox
        #Create a table of all the non-archived projects, each with a checkbox for the option to archive
        table = FORM(SQLTABLE(rows, columns=["Project.id","Project.name","Project.projNum",'Project.openDate',"Project.closedDate"], headers={"Project.id":"Archive","Project.name":"Project Name","Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #"}), INPUT(_type='submit'))
        
        table["_onsubmit"] = "return confirm('Are you sure you want to archive this project?');"
        
        if table.process().accepted:
           response.flash = str(request.vars.name) + ' has been archived'
        elif table.errors:
           response.flash = 'Form has errors'
        else:
           response.flash = 'Select a project to archive'
        
        if table.accepts(request.vars):
            for pID in request.vars.keys():                             #For each project that we want to archive..
                if pID.isdigit():
                    db(db.Project.id == int(pID)).update(archived=True) #Set archived=True for the project and update the database
                    
            redirect(URL('default','manageprojects'))                   #Redirect to the same screen
            
    return dict(table=table, footer=footer, header=header,css=css)

#This is called when an admin clicks "Archived Projects". It returns a dictionary used by the view default/archiveprojects.html    
@auth.requires_login()
@auth.requires_membership('Admin')
def archiveprojects():
    table = None
    rows = db(db.Project.archived == True).select()                     #Get all the archived projects
    
    if len(rows) == 0:
        table = "There are no projects that have been achived."
        
    else:                                                               #There is at least one archived project
        #This column contains the option to view a project when "View" is clicked. It opens a new tab to display the selected project                                                      
        extracolumn = [{'label':'View Archived Project', #label of the entirecolumn
                        'class': '', #class name of the header
                        'width': '', #width in pixels or %
                        'content': lambda row, rc: A("View", _href=URL('default','viewArchive', args=row.id), _target='new'), #what goes in each row
                        'selected': False #aggregate class selected to this column
                       }]
        #Create a table of the archived projects, with the rightmost column containing the extracolumn
        table = SQLTABLE(rows, columns=["Project.name","Project.owner","Project.projNum",'Project.openDate',"Project.closedDate"], headers={"Project.name":"Project Name", "Project.owner":"Owner", "Project.openDate":"Open Date", "Project.closedDate":"Closed Date", "Project.projNum":"Project #"}, extracolumns=extracolumn)
    
    return dict(table=table, footer=footer, header=header, css=css)

#This is called when an admin clicks "View" on the Archived Projects screen. It returns a dictionary used by the view default/viewArchive.html    
@auth.requires_login()
@auth.requires_membership('Admin')
def viewArchive():
    #Get the archived project that the user wants to view (the "archivedprojects" method puts the project id in args)
    project = db(db.Project.id == request.args(0)).select().first() 
    if project != None and not project.archived:     #only view archived projects
        project = None
    return dict(project=project, header=header_archived, css=css)

#This is called when a user clicks on "News Feed" for a project in the sidebar. It returns a dictionary used by the view default/newsfeed.html
@auth.requires_login()
def newsfeed():
    projNum = request.vars.projectNum
    if type(projNum) is list:
        projNum = projNum[-1]
    projectNums = []
    for proj in projects:
        projectNums.append(proj.projNum)
        
    #Check if the project is in the user's projects   
    if int(request.vars.projectNum) in projectNums or auth.has_membership(user_id=auth.user.id, role="Admin"): 
        project = db(db.Project.projNum == request.vars.projectNum).select().first() #Get the current project
        if project != None and  project.archived:    #The user is trying to access an archived project
            return "The project you are trying to view has been archived. If you are an admin and would like to view the project, please go back and click \"Archived Projects.\""
            
        else:       
            #Create an SQLFORM for the user to make a new status update
            form = SQLFORM(db.NewsFeed, labels={'description':'New Status Update'}, fields=['description'])
            form.vars.projectNum = request.vars.projectNum                        #Initialize the project number to be the current project's number
            form.vars.type = "human"                                              #Initialize the type to be" human"
            form.vars.created_on = datetime.today()                               #Initialize the time created to be the current date and time
            form.vars.creator = auth.user.first_name + " " + auth.user.last_name  #Initiaize the creator to be the current user
            
            if form != None:
                if form.process().accepted:
                    response.flash = 'Status created successfully'
                elif form.errors:
                    response.flash = 'Form has errors'
                    
            if myProfileForm.process().accepted:
               response.flash = "Profile updated successfully!"
            elif myProfileForm.errors:
               response.flash = 'Form has errors'    
                       
            #Get all the newsfeed entries, in order, with the most recent entry first
            entries = db(db.NewsFeed.projectNum == request.vars.projectNum).select(orderby=~db.NewsFeed.created_on) 
            if entries == None or len(entries) == 0:                              #If there are no entries, set entries to None
                entries = None
                
            return dict(form=form, entries=entries, fullTable=True, project=project, projects=projects, myProfileForm=myProfileForm, header=header, 
                        footer=footer, css=css,projNum=projNum)
        
    else:   #the user is trying to access a project he's not a part of   
        return "Access Denied"

#This is called when a user clicks on "News Feed" on an archived project's sidebar. It returns a dictionary used by the view default/newsfeedarchived.html
@auth.requires_login()
@auth.requires_membership('Admin')
def newsfeedarchived():
    project = db(db.Project.projNum == request.vars.projectNum).select().first()  #Get the current project
    entries = None
    
    if project != None and not project.archived:                                  #only allow the user to look at an archived project
        project = None
               
    elif project != None and project.archived:                                    #we're looking at a valid archived project
        #Get all the newsfeed entries, in order, with the most recent entry first
        entries = db(db.NewsFeed.projectNum == request.vars.projectNum).select(orderby=~db.NewsFeed.created_on)   
        if entries == None or len(entries) == 0:                                  #If there are no entries, set entries to None
            entries = None   
        
    return dict(entries=entries, fullTable=True, project=project, header=header_archived, css=css)  

# This is called when a user clicks on the "Calendar" tab in a project
@auth.requires_login()
def viewcalendar():
    projectNum = request.vars.projectNum
    project =  db.executesql('SELECT * FROM project WHERE projNum = %s' % projectNum, as_dict=True)
    projName = project[0]['name']

    url = 'https://accounts.google.com/o/oauth2/token'
    refTok = '1/BJ7iFL7rY6Kcyg4zAjX7nON2RO1GkBt-uEDefKgFn78'

    params = urllib.urlencode({
      'client_id': '553030639714.apps.googleusercontent.com',
      'client_secret': 'ZcZQAPsUOfO9F4Eeo-hZ-G-V',
      'refresh_token':refTok,
      'grant_type':'refresh_token'
    })
    response = urllib2.urlopen(url, params).read()

    loaded = json.loads(response)
    auth = "Bearer %s" % str(loaded['access_token'])
    
    url = 'https://www.googleapis.com/calendar/v3/users/me/calendarList'
    calrequest = urllib2.Request(url)
    calrequest.add_header("Authorization",auth)

    calendars = urllib2.urlopen(calrequest).read()
    loaded = json.loads(calendars)

    calID = ''
    for i in loaded['items']:
        if i['summary'] == "Sample Project":
            calID = i['id']
            break

    today = datetime.today()
    first_of_month = date(today.year,today.month,1)

    months = {'1' : "Jan", '2' : "Feb", '3' : "Mar", '4' : "Apr", '5' : "May", "6" : "Jun", '7' : "Jul", '8' : "Aug", '9' : "Sep", '10' : "Oct", "11" : "Nov", "12" : "Dec"}
    year = today.year
    current_month = today.month
    month_form = "<form id='delete_months' action='changemonth.html'>\n<select name='month'>\n"

    embed_date = ''
    selected_month = str(current_month)+ "-" + str(year)
    if request.vars.has_key("month"):
        selected_month = request.vars.month
        tmpSplit = selected_month.split('-')
        first_of_month = date(int(tmpSplit[1]),int(tmpSplit[0]),1)
        if int(tmpSplit[0]) < 10:
            date_month = "%s0%s01" % (tmpSplit[1],tmpSplit[0]) 
        else:
            date_month = "%s%s01" % (tmpSplit[1],tmpSplit[0])
        embed_date = "&dates=" + date_month + '%2F' + date_month
    for i in range(20):
        month_value = str(current_month) + "-" + str(year)
        if selected_month == month_value:
            month_form += "<option value='%s' selected>" % (month_value)
        else:
            month_form += "<option value='%s'>" % (month_value)
        month_form += "%s %s</option>\n" % (months[str(current_month)],str(year))
        current_month = current_month + 1
        if current_month > 12:
            current_month = 1
            year += 1

    month_form += "<input type='hidden' name='projNum' value='%s'/>\n<input type='submit' value='Change Month'/>\n</select>\n</form>" % projectNum

    form_html = get_delete_list(auth, calID, first_of_month)

    return dict(calID = calID, 
        projNum = projectNum, 
        projects=projects, 
        footer=footer, 
        header=header, 
        css=css, 
        embed_date = embed_date,
        form_html = HTML('',XML(form_html)),
        month_html = HTML('',XML(month_form)))

# A helper function for viewcalendar that gets the list of events for a given month from google
def get_delete_list(auth,calID,first_of_month):
    url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events' % calID

    start_month = str(first_of_month) + "T00:00:00.000Z"
    end_month = str(first_of_month + relativedelta(months=1)) + "T00:00:00.000Z"

    params = urllib.urlencode({
      'orderBy': 'startTime',
      'singleEvents': 'true',
      'timeMax': end_month,
      'timeMin':start_month
    })

    url = url + "?" + params

    request = urllib2.Request(url)
    request.add_header("Authorization",auth)

    calendars = urllib2.urlopen(request).read()
    loaded = json.loads(calendars)
    form_html = ''
    if loaded.has_key("items"):
        for i in loaded['items']:
            form_html += "<input type='checkbox' name='delete_item' value='" + i['id'] + "'> Title: " + i['summary'] + '<br>\n'
            start_datetime = datetime.strptime(i['start']['dateTime'][:16], '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(i['end']['dateTime'][:16], '%Y-%m-%dT%H:%M')
            if start_datetime.date() == end_datetime.date():
                form_html += start_datetime.strftime("%m/%d %I:%M %p") + " - " + end_datetime.strftime("%I:%M %p") + '<br><br>\n'
            else:
                form_html += start_datetime.strftime("%m/%d %I:%M %p") + " - " + end_datetime.strftime("%m/%d %I:%M %p") + '<br><br>\n'
        form_html += "<input type='hidden' name='calID' value='%s'/>" % calID
    else:
        form_html = "<span>There are currently no events this month</span>"

    return form_html

def changemonth():
    month = request.vars.month
    projNum = request.vars.projNum
    redirect(URL(viewcalendar, vars = dict(projectNum = projNum, month = month)))

def deleteevent():    
    delete_item = request.vars.delete_item
    projNum = request.vars.projNum
    calID = request.vars.calID

    url = 'https://accounts.google.com/o/oauth2/token'
    refTok = '1/BJ7iFL7rY6Kcyg4zAjX7nON2RO1GkBt-uEDefKgFn78'

    params = urllib.urlencode({
      'client_id': '553030639714.apps.googleusercontent.com',
      'client_secret': 'ZcZQAPsUOfO9F4Eeo-hZ-G-V',
      'refresh_token':refTok,
      'grant_type':'refresh_token'
    })
    response = urllib2.urlopen(url, params).read()

    loaded = json.loads(response)
    auth = "Bearer %s" % str(loaded['access_token'])

    if type(delete_item) is list:
        for i in delete_item:
            url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events/%s' % (calID,i)
            calrequest = urllib2.Request(url)
            calrequest.add_header("Authorization",auth)
            calrequest.get_method = lambda: 'DELETE'

            calendars = urllib2.urlopen(calrequest).read()
    else:
        url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events/%s' % (calID,delete_item)
        calrequest = urllib2.Request(url)
        calrequest.add_header("Authorization",auth)
        calrequest.get_method = lambda: 'DELETE'

        calendars = urllib2.urlopen(calrequest).read()

    redirect(URL(viewcalendar, vars = dict(projectNum = projNum)))



@auth.requires_login()
def addevent():
    summary = request.vars.title
    start_date = request.vars.start_date
    end_date = request.vars.end_date
    location = request.vars.location
    start_time = request.vars.start_time
    end_time = request.vars.end_time
    description = request.vars.description
    calID = request.vars.calID
    projNum = request.vars.projNum

    combine_start = start_date + ' ' + start_time
    combine_end = end_date + ' ' + end_time
 
    start_datetime = datetime.strptime(combine_start, '%m/%d/%Y %I:%M%p')
    end_datetime = datetime.strptime(combine_end, '%m/%d/%Y %I:%M%p')
    
    start = {"dateTime" : start_datetime.isoformat('T'), "timeZone" : "America/Chicago"}
    end = {"dateTime" : end_datetime.isoformat('T'), "timeZone" : "America/Chicago"}
    
    url = 'https://accounts.google.com/o/oauth2/token'
    refTok = '1/BJ7iFL7rY6Kcyg4zAjX7nON2RO1GkBt-uEDefKgFn78'

    params = urllib.urlencode({
      'client_id': '553030639714.apps.googleusercontent.com',
      'client_secret': 'ZcZQAPsUOfO9F4Eeo-hZ-G-V',
      'refresh_token':refTok,
      'grant_type':'refresh_token'
    })
    response = urllib2.urlopen(url, params).read()
    loaded = json.loads(response)

    input_params = {'summary' : summary, 'start' : start, 'end' : end, 'description' : description, 'location' : location}

    data = json.dumps(input_params)
    auth = "Bearer %s" % str(loaded['access_token'])
    
    url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events' % calID
    calrequest = urllib2.Request(url,data)
    calrequest.add_header("Authorization",auth)
    calrequest.add_header("Content-Type",'application/json')

    f = urllib2.urlopen(calrequest)
    response = f.read()
    f.close()

    return dict(projNum = projNum)

#This is called when a user clicks on any of the tabs (to upload/generate a new document). It returns a dictionary used by the view default/showform.html
@auth.requires_login() 
def showform():
    projNum = request.vars.projectNum
    if type(projNum) is list:
        projNum = projNum[-1]
        
    projectNums = []
    for proj in projects:
        projectNums.append(proj.projNum)    
        
    #Check if the project is in the user's projects   
    if int(projNum) in projectNums or auth.has_membership(user_id=auth.user.id, role="Admin"): 
        project = db(db.Project.projNum == projNum).select().first() #Get the current project
        if project != None and project.archived:    #The user is trying to access an archived project
            return "The project you are trying to view has been archived. If you are an admin and would like to view the project, please go back and click \"Archived Projects.\""
            
        else:       
            displayForm = request.vars.displayForm                                       #Get the type of form we want to display
            form = None                                                                  #The SQLFORM that we will display
        
            if displayForm == "CCD":
                #Create a form with all the CCD fields
                form = SQLFORM(db.CCD, labels={'projectNum': "Project #", 'ccdNum':'CCD #'}, fields=['projectNum', 'ccdNum', 'file']) 
                rows = db(db.CCD.projectNum == str(projNum)).select()    #Get all the CCD's for the current project
                form.vars.ccdNum = len(rows) + 1               #Initialize the form's CCD number to be one more than the current number of CCDs               
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number
                
            elif displayForm == "RFI":
                #Create a dropdown of all the users' names for the Request Referred To field
                db.RFI.reqRefTo.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s'+' '+'%(last_name)s')
                #Create a form with the RFI fields specified by the fields parameter
                form = SQLFORM(db.RFI, labels={'rfiNum':'RFI #','projectNum':"Project #", 'requestBy':'Request by', 'dateSent':'Date Sent', 
                    'reqRefTo':'Request Referred to', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #', 
                    'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':
                    'Contractor\'s Suggestion', 'responseBy':'Need Response By'}, fields=['projectNum','rfiNum','requestBy', 'dateSent', 
                    'reqRefTo', 'drawingNum', 'detailNum', 'sheetName', 'grids', 'specSection', 'sectionPage', 'description', 'suggestion', 'responseBy'])
                
                currentProj = db(db.Project.projNum == str(projNum)).select().first()
                rows = db(db.RFI.projectNum == str(projNum)).select()    #Get all the RFI's for the current project       
                form.vars.rfiNum = len(rows) + 1               #Initialize the form's RFI number to be one more than the current number of RFIs
                form.vars.requestBy = auth.user.first_name + " " + auth.user.last_name #Initialize the form's RequestBy field to be the current user
                form.vars.statusFlag = "Outstanding"           #Set the status flag (this field isn't displayed on the screen)
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number 
                form.vars.projectName = currentProj.name       #Set the form's project name to be the current project's name (not displayed)
                form.vars.owner = currentProj.owner            #Set the form's project owner to be the current project's owner (not displayed)
                        
            elif displayForm == "Submittal":
                #Create a dropdown for the submittal type
                db.Submittal.subType.requires = IS_IN_SET(['Samples','Shop Drawing','Product Data'])
                #Create a dropdown of all the users' names for the Assigned To field
                db.Submittal.assignedTo.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s'+' '+'%(last_name)s')
                #Create a dropdown for the status flag
                db.Submittal.statusFlag.requires = IS_IN_SET(['Approved','Resubmit','Approved with Comments','Submitted for Review'])
                #Create a form with all the submittal fields
                form = SQLFORM(db.Submittal, labels={'statusFlag':'Status Flag', 'projectNum':'Project #', 'subType':'Submittal Type', 'sectNum':'Section Number','assignedTo':'Assigned to'}, fields=['projectNum', 'subType', 'assignedTo', 'statusFlag', 'sectNum', 'submittal']) 
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number
                
            elif displayForm == "ProposalRequest":  
                #Create a form with the Proposal Request fields specified by the fields parameter   
                form = SQLFORM(db.ProposalRequest, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 'projectNum':'Project #', 
                    'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 'cc':'CC', 'description':'Description'}, 
                    fields =['projectNum', 'reqNum','amendNum','subject','propDate','sentTo','cc','description'])
                
                currentProj = db(db.Project.projNum == str(projNum)).select().first()
                rows = db(db.ProposalRequest.projectNum == str(projNum)).select() #Get all the ProposalRequests for the current project
                form.vars.reqNum = len(rows) + 1               #Initialize the request number to be one more than the current number of proposal requests
                form.vars.statusFlag = "Open"                  #Set the status flag (this field isn't displayed on the screen)       
                form.vars.creator = auth.user.id               #Initialize the creator to be the current user's id (this field also isn't displayed)
                form.vars.projectNum = projNum                 #Initialize the form's project number to be the current project's number
                form.vars.projectName = currentProj.name       #Set the form's project name to be the current project's name (not displayed)
                form.vars.owner = currentProj.owner            #Set the form's project owner to be the current project's owner (not displayed)
                
            elif displayForm == "Proposal":
                propReqs = db(db.ProposalRequest.projectNum == str(projNum)).select()
                propNumList = []
                for propReq in propReqs:
                    propNumList.append(propReq.reqNum)                   #Get all the Proposal Request numbers for the project
                db.Proposal.propReqRef.requires = IS_IN_SET(propNumList) #Create a dropdown for the Proposal Request Reference #
                #Create a form with all the Proposal fields 
                form = SQLFORM(db.Proposal, labels={'propNum':'Proposal #', 'propReqRef':'Proposal Request Reference #', 'projectNum':'Project #', 
                    'propDate':'Proposal Date'}, fields=['projectNum','propNum','propDate','propReqRef','file'])
                
                rows = db(db.Proposal.projectNum == str(projNum)).select() #Get all the Proposals for the current project
                form.vars.propNum = len(rows) + 1              #Initialize the proposal number to be one more than the current number of proposals
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number
                
            elif displayForm == "MeetingMinutes":
                #Create a form with all the MeetingMinutes fields
                form = SQLFORM(db.MeetingMinutes, labels={'projectNum':'Project #','meetDate':'Meeting Date'})
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number
                
            elif displayForm == "Photo": 
                #Create a form with the Photo fields specified by the fields parameter                     
                form = SQLFORM(db.Photos, labels={'projectNum':'Project #', 'title':'Title', 'description':'Description', 'photo':'Photo'}, 
                    fields = ['projectNum','title','description','photo'])
                form.vars.projectNum = projNum #Initialize the form's project number to be the current project's number
                
            if form != None:                      
                if form.process(onvalidation=checkValidProjNum).accepted:  #The projNum the user entered in the form is a project they are a part of
                    response.flash = 'Form accepted'
                    if displayForm == "Photo": #If submitted form is a photo form, need to upload it to flickr and delete the photo from our database
                        uploadPhotoToFlickr(form)
                    elif displayForm == "RFI": #If submitted form is an RFI form, need to put the name of person the RFI is referred to instead of the id
                        reqUser = db(db.auth_user.id == form.vars.reqRefTo).select().first()
                        row = db(db.RFI.id == form.vars.id).select().first()
                        row.update_record(reqRefTo = reqUser.first_name + " " + reqUser.last_name)
                    elif displayForm == "Submittal": #If submitted form is a Submittal, need to put the name of person it is assigned to instead of the id
                        assignTo = db(db.auth_user.id == form.vars.assignedTo).select().first()
                        row = db(db.Submittal.id == form.vars.id).select().first()
                        row.update_record(assignedTo= assignTo.first_name + " " + assignTo.last_name)
                    
                    #Now create a new newsfeed update noting the new submission
                    if displayForm == "ProposalRequest":
                      displayForm = "Proposal Request"  
                    elif displayForm == "MeetingMinutes":
                        displayForm = "Meeting Minutes document"
                    description = "A new " + displayForm + " has been added."
                    db.NewsFeed.insert(projectNum=form.vars.projectNum, type="document", created_on=datetime.today(), description=description, 
                        creator=auth.user.first_name + " " + auth.user.last_name)
                    db.commit()
                    redirect(URL("default","showform", vars={"displayForm":request.vars.displayForm,"projectNum":projNum}))
            elif form.errors:
                response.flash = 'Form has errors'
            else:
                response.flash = 'Please fill out the form'
                    
            return dict(displayForm=displayForm,
                        form=form,
                        myProfileForm=myProfileForm,
                        projects=projects,
                        footer=footer,
                        header=header,
                        css=css,
                        projNum=projNum)
    else:    #the user is trying to access a project he's not a part of   
        return "Access Denied"

#This is called by showform on validation to make sure the project number the user entered is for a project they are associated with
def checkValidProjNum(form):
    projectNums = []
    for proj in projects:
        projectNums.append(proj.projNum)
    if not int(form.vars.projectNum) in projectNums:    #The user is trying to submit a form to a projct he's not a part of
        form.errors.projectNum = "You do not have access to this project"  
    
#This is called when a user clicks on a categry in an archived project's sidebar. It returns a dictionary used by the view default/formtablearchived.html
@auth.requires_login()
@auth.requires_membership('Admin') 
def formtablearchived():
    formType = request.vars.formType                                              #Get the type of table to display
    project =  db(db.Project.projNum == request.vars.projectNum).select().first() #Get the archived project that is currently being viewed
    table = None                                                                  #The SQLTABLE we will be displaying - set depending on the formType
    fullTable = True                                                              #Keeps track if there are entries for the category or not
    rows = None
    
    if project != None and not project.archived:                                  #Only want to allow viewing of  archived projects
        project = None
    else:
        if formType == "CCD":
            rows = db(db.CCD.projectNum == str(request.vars.projectNum)).select() #Get all the CCDs for the current project
            for row in rows:
                row.file = str(URL('default','download',args=row.file))[1:]       #Set the CCD's file URL
            #Create a table of the CCDs, displaying the values given by the columns parameter
            table = SQLTABLE(rows,columns=["CCD.ccdNum",'CCD.file'],headers={"CCD.ccdNum":"CCD #","CCD.file":"CCD File"},upload="http://127.0.0.1:8000")
        
        elif formType == "RFI":
            rows = db(db.RFI.projectNum == str(request.vars.projectNum)).select() #Get all the RFIs for the current project
            #Represent the RFI number as a link to view the RFI
            db.RFI.rfiNum.represent = lambda rfiNum: A(str(rfiNum), _href=URL("default","create_odt",args=[int(rfiNum)]),_target="_blank")
            #Create a table of the RFIs
            table = SQLTABLE(rows, _width="800px", columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.responseDate"], 
                headers={"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To","RFI.responseDate":"Response Date"})
        
        elif formType == "Submittal":
            rows = db(db.Submittal.projectNum == str(request.vars.projectNum)).select() #Get all the Submittals for the current project
            for row in rows:
                row.submittal = str(URL('default','download',args=row.submittal))[1:]   #Set the Submittal's file URL
            #Create a table of the Submittals 
            table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.subType","Submittal.sectNum","Submittal.submittal"], 
                headers={"Submittal.assignedTo":"Assigned To","Submittal.subType":"Type","Submittal.sectNum":"Section Number",
                "Submittal.submittal":"Submitted File"}, upload="http://127.0.0.1:8000")
        
        elif formType == "ProposalRequest":
            rows = db(db.ProposalRequest.projectNum == str(request.vars.projectNum)).select() #Get all the Proposal Requests for the current project
            #Create a table of the Proposal Requests
            table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.sentTo","ProposalRequest.propDate"],
                headers={"ProposalRequest.reqNum":"Request Number","ProposalRequest.amendNum":"Amendment Number",
                "ProposalRequest.sentTo":"Sent To","ProposalRequest.propDate":"Proposal Request Date"})
        
        elif formType == "Proposal":
            rows = db(db.Proposal.projectNum == str(request.vars.projectNum)).select()  #Get all the Proposals for the current project
            for row in rows:
                row.file = str(URL('default','download',args=row.file))[1:]             #Set the Proposal's file URL
            #Create a table of the Proposals
            table = SQLTABLE(rows, columns=["Proposal.propNum","Proposal.propReqRef","Proposal.propDate","Proposal.file"], 
                headers={"Proposal.propNum":"Proposal Number","Proposal.propReqRef":"Proposal Request Reference Number",
                "Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"}, upload="http://127.0.0.1:8000")
        
        elif formType == "MeetingMinutes":
            rows = db(db.MeetingMinutes.projectNum == str(request.vars.projectNum)).select() #Get all the Meeting Minutes for the current project
            for row in rows:
                row.file = str(URL('default','download',args=row.file))[1:]                  #Set the Meeting Minute's file URL
            #Create a table of the Meeting Minutes
            table = SQLTABLE(rows, columns=["MeetingMinutes.meetDate","MeetingMinutes.file"], 
                headers={"MeetingMinutes.meetDate":"Meeting Date","MeetingMinutes.file":"Submitted File"}, upload="http://127.0.0.1:8000")
        
        elif formType == "Photo":    
            rows = db(db.Photos.projectNum == str(request.vars.projectNum)).select()    #Get all the Photos for the current project
            #Make the flickrURL a link to open the photo in flickr with a new tab
            db.Photos.flickrURL.represent = lambda flickrURL: A("View Photo", _href=flickrURL, _target="_blank")
            #Create a table of the Photos' information
            table = SQLTABLE(rows, columns=["Photos.title","Photos.description","Photos.flickrURL"], 
                headers={"Photos.title":"Title", "Photos.description":"Description","Photos.flickrURL":"Photo"})
    
        if rows == None:                                                                #The url has an invalid formType
            table = "Not a valid form type"
            fullTable = False
        elif len(rows) == 0:                                                            #There are no db entries for the type
            table = "There were no documents uploaded for this project section."
            fullTable = False

    return dict(formType=formType,
                project=project,
                table=table,
                header=header_archived,
                css=css,
                fullTable=fullTable)

#This is called when a user clicks on a category for a project in the sidebar. It returns a dictionary used by the view default/formtable.html
@auth.requires_login()
def formtable():
    projNum = request.vars.projectNum
    if type(projNum) is list:                                                #If projNum is a list, get the last number
        projNum = projNum[-1]
        
    projectNums = []
    for proj in projects:                                                    #Get the project numbers for the user's projects
        projectNums.append(proj.projNum)
        
    #Check if the project is in the user's projects  
    if int(projNum) in projectNums or auth.has_membership(user_id=auth.user.id, role="Admin"):
        project = db(db.Project.projNum == projNum).select().first()         #Get the current project
        if project != None and project.archived:                             #The user is trying to access an archived project
            return "The project you are trying to view has been archived. If you are an admin and would like to view the project, please go back and click \"Archived Projects.\""
            
        else:  
            formType = request.vars.formType                                 #Get the type of table to display        
            table = None                                                     #The SQLTABLE we will be displaying - set depending on the formType
            fullTable = True                                                 #Keeps track if there are entries for the category or not
            rows = None
            
            if formType == "CCD":
                rows = db(db.CCD.projectNum == projNum).select()             #Get all the CCDs for the current project
                for row in rows:
                    row.file = str(URL('default','download',args=row.file))[1:]  #Set the CCD file's URL
                #myextracolumns = [{'label': 'CCD Thumbnail(for testing)','class':'','selected':False, 'width':'', 
                #    'content': lambda row, rc: IMG(_width="40",_height="40",_src=URL('default','download',args=row.file))}]
                #Create a table of the CCDs
                table = SQLTABLE(rows,columns=["CCD.ccdNum",'CCD.file'], headers={"CCD.ccdNum":"CCD #","CCD.file":"CCD File"}, upload="http://127.0.0.1:8000")
            
            elif formType == "RFI":
                rows = db(db.RFI.projectNum == str(projNum)).select()        #Get all the RFIs for the current project
                #Create an extra column. If the user is the one who is supposed to reply to the RFI, then have a link in the column for the user to do so
                extracolumn = [{'label':'Reply to RFI',
                        'class': '', #class name of the header
                        'width': '', #width in pixels or %
                        'content':lambda row, rc: A("Reply", _href=URL('default','replyRFI',args=row.id)) if auth.user.first_name +" " +
                             auth.user.last_name == row.reqRefTo else A(" "),  #What actually goes in the column
                        'selected': False #aggregate class selected to this column
                        }]
                #Create a table of the RFIs, adding the extra "Reply to RFI" column on the far right
                table = SQLTABLE(rows,_width="800px", columns=["RFI.rfiNum","RFI.dateSent","RFI.reqRefTo","RFI.responseBy","RFI.responseDate",
                    "RFI.statusFlag"], headers={"RFI.rfiNum":"RFI #","RFI.dateSent":"Date Sent","RFI.reqRefTo":"Request Referred To",
                    "RFI.responseDate":"Response Date","RFI.responseBy":"Need Response By","RFI.statusFlag":"Status Flag"}, extracolumns=extracolumn)
            
            elif formType == "Submittal":
                rows = db(db.Submittal.projectNum == projNum).select()       #Get all the Submittals for the current project
                for row in rows:
                    row.submittal = str(URL('default','download',args=row.submittal))[1:]  #Set the Submittals' file URL
                #Create a table of the Submittals
                table = SQLTABLE(rows, columns=["Submittal.assignedTo","Submittal.statusFlag","Submittal.subType","Submittal.sectNum","Submittal.submittal"],
                    headers={"Submittal.assignedTo":"Assigned To","Submittal.statusFlag":"Status Flag","Submittal.subType":"Type",
                    "Submittal.sectNum":"Section Number","Submittal.submittal":"Submitted File"}, upload="http://127.0.0.1:8000")
            
            elif formType == "ProposalRequest":
                rows = db(db.ProposalRequest.projectNum == projNum).select() #Get all the Proposal Requests for the current project
                #Create an extra column. If the user is the creator of the request, include a link with the option to change the status of the document 
                extracolumn = [{'label':'Change Status',
                        'class': '', #class name of the header
                        'width': '', #width in pixels or %
                        'content':lambda row, rc: A("Change", _href=URL('default','changePropReq',args=row.id)) if auth.user.id == row.creator else A(" "),
                        'selected': False #aggregate class selected to this column
                        }]
                #Create a table of the Proposal Requests
                table = SQLTABLE(rows, columns=["ProposalRequest.reqNum","ProposalRequest.amendNum","ProposalRequest.statusFlag",
                    "ProposalRequest.sentTo","ProposalRequest.propDate"], headers={"ProposalRequest.reqNum":"Request Number",
                    "ProposalRequest.amendNum":"Amendment Number","ProposalRequest.sentTo":"Sent To","ProposalRequest.statusFlag":"Status Flag",
                    "ProposalRequest.propDate":"Proposal Request Date"}, extracolumns=extracolumn)
            
            elif formType == "Proposal":
                rows = db(db.Proposal.projectNum == projNum).select()        #Get all the Proposals for the current project
                for row in rows:
                    row.file = str(URL('default','download',args=row.file))[1:]   #Set the Proposals' file URL
                #Create a table of the Proposals
                table = SQLTABLE(rows, columns=["Proposal.propNum","Proposal.propReqRef","Proposal.propDate","Proposal.file"],
                    headers={"Proposal.propNum":"Proposal Number","Proposal.propReqRef":"Proposal Request Reference Number",
                    "Proposal.propDate":"Proposal Date","Proposal.file":"File Submitted"}, upload="http://127.0.0.1:8000")
            
            elif formType == "MeetingMinutes":
                rows = db(db.MeetingMinutes.projectNum == projNum).select()  #Get all the Meeting Minutes for the current project
                for row in rows:
                    row.file = str(URL('default','download',args=row.file))[1:]   #Set the Meeting Minutes' file URL
                #Create a table of the Meeting Minutes
                table = SQLTABLE(rows, columns=["MeetingMinutes.meetDate","MeetingMinutes.file"],
                    headers={"MeetingMinutes.meetDate":"Meeting Date","MeetingMinutes.file":"Submitted File"}, upload="http://127.0.0.1:8000")
            
            elif formType == "Photo":    
                rows = db(db.Photos.projectNum == projNum).select()          #Get all the Photos for the current project
                #Make the flickrURL a link to open the photo in flickr with a new tab
                db.Photos.flickrURL.represent = lambda flickrURL: A("View Photo", _href=flickrURL, _target="_blank")
                #Create a table of the Photos' information
                table = SQLTABLE(rows, columns=["Photos.title","Photos.description","Photos.flickrURL"], 
                    headers={"Photos.title":"Title", "Photos.description":"Description","Photos.flickrURL":"Photo"})
        
            if rows == None:                                                 #The url's formType is not valid
                table = "Not a valid form type"
                fullTable = False
            elif len(rows) == 0:                                             #There are no db entries for the type
                table = "There are no documents uploaded for this project section yet."
                fullTable = False       
                
            if myProfileForm.process().accepted:
               response.flash = "Profile updated successfully!"
            elif myProfileForm.errors:
               response.flash = 'Form has errors'
        
            return dict(formType=formType,
                        myProfileForm=myProfileForm,
                        projects=projects,
                        table= table,
                        footer=footer,
                        header=header,
                        css=css,
                        fullTable=fullTable)
                    
    else:    #The user is trying to access a project that he's not a part of
        return "Access Denied"
    
#This is called when a user clicks on "Reply to RFI" when on the RFI's formtable view. It returns a dictionary used by the view default/replyRFI.html
@auth.requires_login()
def replyRFI():
    id = request.args(0) #the id of the RFI
    
    rfiIds = []                                                              #Get all the rfi's that the user is able to reply to
    for project in projects:
        rfis = db(db.RFI.projectNum == str(project.projNum)).select()
        for rfi in rfis:
            if rfi.reqRefTo == auth.user.first_name + " " + auth.user.last_name:
                rfiIds.append(rfi.id)
    
    if int(id) in rfiIds:                                                    #The user is replying to an rfi that they're supposed to reply to
        db.RFI.statusFlag.requires = IS_IN_SET(['Outstanding','Closed'])     #Make a dropdown for the status flag
        db.RFI.responseDate.requires = IS_NOT_EMPTY(error_message="Choose the correct date")
        
        #Create the SQLFORM, filling in all the previously submitted information
        replyRfiForm = SQLFORM(db.RFI, id, showid=False, labels={'rfiNum':'RFI #','projectNum':"Project #", 'requestBy':'Request by', 
            'dateSent':'Date Sent', 'reqRefTo':'Request Referred to', 'drawingNum':'Drawing #', 'detailNum':'Detail #', 'specSection':'Spec Section #',
            'sheetName':'Sheet Name', 'grids':'Grids', 'sectionPage':'Section Page #', 'description':'Description', 'suggestion':
            'Contractor\'s Suggestion', 'responseBy':'Need Response By', 'reply':'Reply', 'responseDate':'Response Date', 'statusFlag':'Status Flag'}, 
            fields = ['rfiNum','projectNum','requestBy', 'dateSent', 'reqRefTo', 'drawingNum', 'detailNum', 'specSection', 'sheetName', 'grids',
            'sectionPage', 'description', 'suggestion', 'responseBy', 'reply', 'responseDate', 'statusFlag'], _id="replyForm")
        
        if replyRfiForm != None:
            if replyRfiForm.process().accepted:
                row = db(db.RFI.id == id).select().first()                     #Get the RFI we're replying to
                
                #Update the RFI's reply and response date (but don't save any of the other fields -- want to keep the other fields read-only for this)
                row.update_record(reply=str(replyRfiForm.vars.reply), responseDate=str(replyRfiForm.vars.responseDate))     
                db.commit()   
                
                session.flash = T('RFI Reply Accepted')  
                redirect(URL('default', 'formtable', vars=dict(formType='RFI', projectNum=str(replyRfiForm.vars.projectNum)))) #Redirect to the RFI table                    
            
            elif replyRfiForm.errors:
                response.flash = 'Form has errors'
            else:
                response.flash = 'Please fill out the reply, response date, and status flag'
                
        return dict(replyRfiForm=replyRfiForm, css=css, header=header, footer=footer)
        
    else:                                                                    #The user is tying to reply to an rfi they're not supposed to reply to
        return "Access Denied"
    
#This is called when a user clicks on "Change Status" when on the Proposal Request's formtable view. It returns a dictionary used by the view default/changePropReq.html
@auth.requires_login()
def changePropReq():
    id = request.args(0)  #The id of the Proposal Request
    
    prIds = []
    for project in projects:                                                #Get the propReqs that the user created
        reqs = db(db.ProposalRequest.projectNum == str(project.projNum)).select()
        for req in reqs:
            if req.creator == auth.user.id:
                prIds.append(req.id)
    
    if int(id) in prIds:                                                    #If the user is allowed to change the proposal request
        db.ProposalRequest.statusFlag.requires = IS_IN_SET(['Open','Closed'])     #Make a dropdown for the status flag  
        
        #Create the SQLFORM, filling in all the previously submitted information
        changePropReqForm = SQLFORM(db.ProposalRequest, id, showid=False, labels={'reqNum':'Request #', 'amendNum':'Amendment #', 
            'statusFlag':'Status', 'projectNum':'Project #', 'subject':'Subject', 'propDate':'Proposal Date', 'sentTo':'Sent to', 
            'cc':'CC', 'description':'Description'}, fields =['reqNum','amendNum','projectNum','subject','propDate',
            'sentTo','cc','description','statusFlag'], _id="changePropReqForm")
            
        if changePropReqForm != None:
            if changePropReqForm.process().accepted:
                row = db(db.ProposalRequest.id == id).select().first()      #Get the current Proposal Request
                row.update_record(statusFlag = str(changePropReqForm.vars.statusFlag)) #Update the Proposal Request with the new status flag      
                db.commit()   
                session.flash = T('Status Change Accepted')  
                #Redirect to the Proposal Request table
                redirect(URL('default', 'formtable', vars=dict(formType='ProposalRequest', projectNum=str(changePropReqForm.vars.projectNum))))                      
            elif changePropReqForm.errors:
                response.flash = 'Form has errors'
            else:
                response.flash = 'You may update the status flag'
                
        return dict(changePropReqForm=changePropReqForm, css=css, header=header, footer=footer) 
        
    else:                                                                   #The user is trying to change a propReq he's not allowed to change
        return "Access Denied"

def viewPhoto():
    br = mechanize.Browser()
    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    r = br.open(request.vars["url"])
    br.select_form("login_form")
    br.form["passwd"]="finholt1"
    #import tkMessageBox
    #tkMessageBox.showinfo(title="Greetings", message=str(br.form))
    r = br.submit()
    br.open(request.vars["url"])
   
    redirect(request.vars["url"])        

#This returns a string of the opposite of the user's role (either Admin or General)
def getOtherRoles(id):
    if auth.has_membership(user_id=id, role="Admin"):
        return "General"
    else:
        return "Admin"

#This returns a string of the user's role (either Admin or General)     
def getUserRole(id):
    if auth.has_membership(user_id=id, role="Admin"):
        return "Admin"
    else:
        return "General"

#This is called by create_odt to get a dictionay of RFI data given the RFI number
def get_data(row_id):
    import MySQLdb

    db = MySQLdb.connect(host="10.24.6.23", user="seniorproj", passwd="web2py2012", db="finholt")
    cur = db.cursor()

    # Getting the rows from the database

    cur.execute("SELECT * FROM RFI WHERE rfiNum = %s;",(row_id))
    columns = cur.description
    row = cur.fetchall()

    dict = {}

    for i in range(len(columns)):
        dict[columns[i][0]] = row[0][i]

    return dict

#This creates the RFI document for viewing in the browser. It returns a dictionary used by the view default/create_odt.html
def create_odt():
    import subprocess
    import os
    import time
    appy = local_import('appy.pod.renderer')

    phpscript = os.path.join(request.folder, 'static', 'php', 'result.odt')
    subprocess.Popen("rm " + phpscript, shell=True)

    # giving the program enough time to delete the old result.odt
    time.sleep(1)
 
    dictionary = get_data(request.args[0])

    appyDict = {}
    appyDict['rfiNumber'] = dictionary['rfiNum']

    # Need to add database places for these and then add the dictionary
    appyDict['project'] = dictionary['projectName']
    appyDict['owner'] = dictionary['owner']

    appyDict['requestBy'] = dictionary['requestBy']

    dtSent = dictionary['dateSent']
    if dtSent != None:
        appyDict['DateSent'] = "%s/%s/%s" % (dtSent.month,dtSent.day,dtSent.year)
    else:
        appyDict['DateSent'] = "None"

    appyDict['requestReferredTo'] = dictionary['reqRefTo']

    dtRec = dictionary['dateRec']
    if dtRec != None:
        appyDict['DateReceived'] = "%s/%s/%s" % (dtRec.month,dtRec.day,dtRec.year)
    else:
        appyDict['DateReceived'] = "None"

    appyDict['drawingNum'] = dictionary['drawingNum']

    appyDict['detailNum'] = dictionary['detailNum']

    appyDict['specNum'] = dictionary['specSection']
    appyDict['sheetName'] = dictionary['sheetName']

    appyDict['grids'] = dictionary['grids']
    appyDict['sectionPage'] = dictionary['sectionPage']

    appyDict['rfiDescription'] = dictionary['description']

    appyDict['contractorSuggestion'] = dictionary['suggestion']

    appyDict['reply'] = dictionary['reply']

    appyDict['responseBy'] = dictionary['responseBy']

    dtResp = dictionary['responseDate']
    if dtResp != None:
        appyDict['responseDate'] = "%s/%s/%s" % (dtResp.month,dtResp.day,dtResp.year)
    else:
        appyDict['responseDate']

    myfile = os.path.join(request.folder, 'static','php', 'rfiTemplate.odt')
    newfile = os.path.join(request.folder, 'static','php', 'result.odt')
    
    renderer = appy.Renderer(myfile, appyDict, newfile)
    renderer.run()

    phpscript = os.path.join(request.folder, 'static', 'php', 'rfi.php')
    proc = subprocess.Popen("php " + phpscript, shell=True, stdout=subprocess.PIPE)
    resp = proc.stdout.read()

    return dict(html=HTML('',XML(resp)))

#Returns the html needed for the checkboxes on the addtoproject screen 
def getAllProjectsHtml(id):
    html=''
    projects = db(db.Project.archived == False).select()  #Get all the current non-archived projects
    user = db(db.auth_user.id == id).select().first()     #Get the user given the user's id
    
    if getUserRole(id) == "Admin":                        #The user is an admin
        html = "<p>Is Admin</p>"
    else:
        for row in projects:                              #Find all the projects that the user is not already associated with
            if user.projects != None:
                if row.projNum not in user.projects:
                    html +=  '<input value="'+str(row.projNum)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(row.projNum)+"</br>"
            else:
                html +=  '<input value="'+str(row.projNum)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(row.projNum)+"</br>"
        
        if html =='':                                      #The user is already associated with all the projects
            html = "<p>In all projects</p>"
            
    return html 

#Returns the html needed for the checkboxes on the deletefromproject screen
def getUsersProjectsHtml(id):
    html = ''    
    user = db(db.auth_user.id == id).select().first()     #Get the user given the user's id
    
    if getUserRole(id) == "Admin":                        #The user is an admin
        html = "<p>Is Admin</p>"
    else:
        if user.projects != None and len(user.projects) >= 1: #Make a checkbox for all the projects that the user is associatewith
            for projId in user.projects:
                project = db((db.Project.archived == False) & (db.Project.projNum == projId)).select().first()
                html +=  '<input value="'+str(project.projNum)+'" type="checkbox" name="'+str(user.id)+'"/>'+str(project.projNum)+"</br>"
        else:
            html = "<p>Not on any projects</p>"
        
    return html
