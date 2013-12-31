import sys
import PySide
import ui_mainwindow
import traderthread

class MainWindow(QtGui.QMainWindow):
  ui = Ui_MainWindow()
  def __init_(self):
    super(MainWindow, self).__init_(self)
    self.ui.setupUi(self)
  
  @QtCore.Slot(QtCore.QDateTime, Tops, ArbData, Balance)
  def receiveUpdate(time, tops, arbData:
    pass
    #todo
    
  #todo