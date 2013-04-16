from datetime import datetime
from appy.pod.renderer import *
import MySQLdb

def get_data(row_id):
    db = MySQLdb.connect(host="10.24.6.23",user="seniorproj",passwd="web2py2012",db="finholt")
    cur = db.cursor()

    # Getting the rows from the database

    cur.execute("SELECT * FROM RFI WHERE id = %s;",(row_id))
    columns = cur.description
    row = cur.fetchall()

    dict = {}

    for i in range(len(columns)):
    	dict[columns[i][0]] = row[0][i]

    return dict

def main():
    dict = get_data("1")

    rfiNumber = dict['rfiNum']

    # Need to add database places for these and then add the dict
    project = 'Hemodialysis Unit and Clinic Expansion'
    owner = 'Winneskiek Medical Center'

    requestBy = dict['requestBy']
    print requestBy

    dtSent = dict['dateSent']
    DateSent = "%s/%s/%s" % (dtSent.month,dtSent.day,dtSent.year)
    requestReferredTo = dict['reqRefTo']

    dtRec = dict['dateRec']
    DateReceived = "%s/%s/%s" % (dtRec.month,dtRec.day,dtRec.year)

    drawingNum = dict['drawingNum']

    detailNum = dict['detailNum']

    specNum = dict['specSection']
    sheetName = dict['sheetName']

    grids = dict['grids']
    sectionPage = dict['sectionPage']

    rfiDescription = dict['description']

    contractorSuggestion = dict['suggestion']

    reply = dict['reply']

    responseBy = dict['responseBy']

    dtResp = dict['responseDate']
    responseDate = "%s/%s/%s" % (dtResp.month,dtResp.day,dtResp.year)

    testDict = {}
    testDict['test'] = "Testing 1,2,3..."

    # renderer = Renderer('rfiTemplate.odt', globals(), 'result.odt')
    renderer = Renderer('test.odt', testDict, 'complete.odt')
    renderer.run()

main()
