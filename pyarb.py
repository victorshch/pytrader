import sys
import PyQt4
from PyQt4 import QtCore, QtGui
import traderthread
import mainwindow
import tradeapi

app = QtGui.QApplication(sys.argv)

mainWindow = mainwindow.MainWindow()

mainWindow.show()

tradeApi = None

if(len(sys.argv) > 1 and sys.argv[1] == 'bitfinex'):
  tradeApi = tradeapi.BitfinexTradeApi()
else:
  tradeApi = tradeapi.BTCETradeApi("keyfile.txt")

traderThread = traderthread.TraderThread(app, tradeApi)


traderThread.updateData.connect(mainWindow.receiveUpdate)
app.aboutToQuit.connect(traderThread.quit)
traderThread.start()

sys.exit(app.exec_())