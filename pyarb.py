import sys
import PyQt4
from PyQt4 import QtCore, QtGui
import traderthread
import mainwindow
import tradeapi

app = QtGui.QApplication(sys.argv)

tradeApi = None
exchangeName = ''

if(len(sys.argv) > 1):
  exchangeName = sys.argv[1]
else:
  exchangeName = 'btce'

tradeApi = tradeapi.CreateTradeApi(exchangeName, 'keyfile.txt')  

mainWindow = mainwindow.MainWindow(tradeApi.Name())

mainWindow.show()

traderThread = traderthread.TraderThread(app, tradeApi)

mainWindow.ui.label_sec1.setText(traderThread.p1)
mainWindow.ui.label_sec2.setText(traderThread.p2)
mainWindow.ui.label_sec3.setText(traderThread.p3)

traderThread.updateData.connect(mainWindow.receiveUpdate)
traderThread.updateLag.connect(mainWindow.receiveLag)
app.aboutToQuit.connect(traderThread.quit)
traderThread.start()

sys.exit(app.exec_())