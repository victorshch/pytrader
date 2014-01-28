import sys
import PyQt4
from PyQt4 import QtCore, QtGui
import argparse
import decimal
from decimal import Decimal

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
parser.add_argument("--trade-interval", type=int, default=10000, dest='trade_interval')
parser.add_argument("--usd-to-spend", type=Decimal, default=Decimal('20'), dest='usd_to_spend')
parser.add_argument("--btc-to-spend", type=Decimal, default=Decimal('0.02'), dest='btc_to_spend')
parser.add_argument("--arb-coin-to-spend", type=Decimal, default=Decimal('1'), dest='arb_coin_to_spend')
parser.add_argument("--min-profit", type=Decimal, default=Decimal('0.01'), dest='min_profit')
parser.add_argument("--max-lag", type=int, default=1000, dest='max_lag')
args = parser.parse_args()

exchangeName = args.exchange
coin = args.arb_coin
timeout = args.refresh_timeout

with tradeapi.CreateTradeApi(exchangeName, ['keyfile.txt', 'keyfile2.txt', 'keyfile3.txt']) as tradeApi:
  mainWindow = mainwindow.MainWindow(tradeApi.Name())

  mainWindow.show()

  traderThread = traderthread.TraderThread(app, tradeApi, 'btcusd', coin+'btc', coin+'usd', timeout, args.trade_interval,
  args.usd_to_spend, args.btc_to_spend, args.arb_coin_to_spend, args.min_profit, args.max_lag)

  mainWindow.ui.label_sec1.setText(traderThread.p1)
  mainWindow.ui.label_sec2.setText(traderThread.p2)
  mainWindow.ui.label_sec3.setText(traderThread.p3)

  traderThread.updateData.connect(mainWindow.receiveUpdate, QtCore.Qt.QueuedConnection)
  traderThread.updateLag.connect(mainWindow.receiveLag, QtCore.Qt.QueuedConnection)
  app.aboutToQuit.connect(traderThread.quit)
  traderThread.start()

  sys.exit(app.exec_())