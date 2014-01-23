import gdata.spreadsheet.service

class SpreadsheetHandler(object):
  def __init__(self, keyfile, spreadsheetKey, source):
    self.spreadsheetKey = spreadsheetKey
    
    with open(keyfile) as f:
      lines = f.readlines()
      self.email = lines[0]
      self.password = lines[1]
      
    self.source = source
  
  def getClient(self):
    client = gdata.spreadsheet.service.SpreadsheetsService()
    client.email = self.email
    client.password = self.password
    client.source = self.source
    client.ProgrammaticLogin()
    
    return client
  
  def getSheetId(self, client, sheet):
    wfeed = client.GetWorksheetsFeed(self.spreadsheetKey)
    
    wId = None
    
    for worksheet in wfeed.entry:
      if worksheet.title.text == sheet:
        wId = worksheet.id.text.split('/')[-1]
        break
        
    if wId == None:
      print "Couldn't find sheet %s in spreadsheet" % sheet

    return wId
  
  def AddRow(self, sheetName, row):
    client = self.getClient()
    
    wId = self.getSheetId(client, sheetName)
    if wId == None:
      return False
    
    entry = client.InsertRow({key: str(row[key]) for key in row}, self.spreadsheetKey, wId)
    if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
      return True
    else:
      return False

  def GetSheet(self, sheetName):
    client = self.getClient()
    
    wId = self.getSheetId(client, sheetName)
    if wId == None:
      return []
    
    return [dict( zip( entry.custom.keys(), [ value.text for value in entry.custom.values() ] ) ) \
      for entry in client.GetListFeed( self.spreadsheetKey, wId ).entry]