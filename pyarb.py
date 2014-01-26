import sys
import PyQt4
from PyQt4 import QtCore, QtGui
import argparse

import traderthread
import mainwindow
import tradeapi

app = QtGui.QApplication(sys.argv)

tradeApi = None
exchangeName = ''

parser = argparse.ArgumentParser()
parser.add_argument("--exchange", choices=['btce', 'bitfinex'], default='btce')
parser.add_argument("--arb-coin", choices=['ltc', 'nmc', 'ppc', 'nvc'], default='ltc', dest='arb_coin')
parser.add_argument("--refresh-timeout", type=int, default=100, dest='refresh_timeout')
args = parser.parse_args()

exchangeName = args.exchange
coin = args.arb_coin
timeout = args.refresh_timeout

tradeApi = tradeapi.CreateTradeApi(exchangeName, ['keyfile.txt', 'keyfile2.txt', 'keyfile3.txt'])  

mainWindow = mainwindow.MainWindow(tradeApi.Name())

mainWindow.show()

traderThread = traderthread.TraderThread(app, tradeApi, 'btcusd', coin+'btc', coin+'usd', timeout)

mainWindow.ui.label_sec1.setText(traderThread.p1)
mainWindow.ui.label_sec2.setText(traderThread.p2)
mainWindow.ui.label_sec3.setText(traderThread.p3)

traderThread.updateData.connect(mainWindow.receiveUpdate, QtCore.Qt.QueuedConnection)
traderThread.updateLag.connect(mainWindow.receiveLag, QtCore.Qt.QueuedConnection)
app.aboutToQuit.connect(traderThread.quit)
traderThread.start()

sys.exit(app.exec_())