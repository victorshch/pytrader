import sys
import decimal
from decimal import Decimal
import PyQt4
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import pyqtSignal

class Tops(object):
  ask1 = Decimal('0')
  ask1_amount = Decimal('0')
  bid1 = Decimal('0')
  bid1_amount = Decimal('0')
  ask2 = Decimal('0')
  ask2_amount = Decimal('0')
  bid2 = Decimal('0')
  bid2_amount = Decimal('0')
  ask3 = Decimal('0')
  ask3_amount = Decimal('0')
  bid3 = Decimal('0')
  bid3_amount = Decimal('0')
  
class ArbData(object):
  def __init__(self, direction = "Forward", p = 0, usdProfit = 0, usdInvestment = 0):
    self.tradeDirection = direction
    self.profit = p
    self.usdProfit = usdProfit
    self.usdInvestment = usdInvestment
  
class Balance(object):
  balance_usd = 0
  balance_ltc = 0
  balance_btc = 0

class TraderThread(QtCore.QThread):
  timer = QtCore.QTimer()
  stopwatch = QtCore.QTime()
  tradeTimer = QtCore.QTimer()
  updateData = pyqtSignal(Tops, ArbData, ArbData)
  updateLag = pyqtSignal(int)
  def __init__(self, parent, tradeAPI, p1='btcusd', p2='ltcbtc', p3 = 'ltcusd', refreshInterval=100, tradeInterval=15000):
    super(TraderThread, self).__init__(parent)
    self.tradeAPI = tradeAPI
    self.k = Decimal('1') - (tradeAPI.Comission() / Decimal('100.0'))
    self.p1 = p1
    self.p2 = p2
    self.p3 = p3
    self.timer.setInterval(refreshInterval)
    self.timer.setSingleShot(True)
    self.tradeTimer.setInterval(tradeInterval)
    self.tradeTimer.setSingleShot(True)
    self.timer.timeout.connect(self.onTimer)

  @pyqtSlot()
  def onTimer(self):
    
    self.stopwatch.start()
    t = self.GetTops()
    elapsed = self.stopwatch.elapsed()
    self.updateLag.emit(elapsed)
    
    a1, b1 = t.ask1, t.bid1
    a2, b2 = t.ask2, t.bid2
    a3, b3 = t.ask3, t.bid3
    
    k3 = self.k * self.k * self.k
    
    profit1 = k3 * (b3) / ((a1) * (a2)) - Decimal('1.0')
    profit2 = k3 * (b1) * (b2) / (a3)  - Decimal('1.0')
    
    a1 = ArbData("Forward", profit1)
    a2 = ArbData("Backward", profit2)

    self.updateData.emit(t, a1, a2)
    
    self.timer.start()

  def run(self):
    self.timer.start()
    self.exec_()
  
  def GetTop(self, pair):
    r = self.tradeAPI.GetDepth(pair, 1, 1)
    return ((r['ask'][0]['price'], r['ask'][0]['amount']), (r['bid'][0]['price'], r['bid'][0]['amount']))
  
  def GetTops(self):
    result = Tops()
    r = self.tradeAPI.GetDepths([self.p1, self.p2, self.p3], 1, 1, 5)
    p1Top = ((r[self.p1]['ask'][0]['price'], r[self.p1]['ask'][0]['amount']), (r[self.p1]['bid'][0]['price'], r[self.p1]['bid'][0]['amount']))
    p2Top = ((r[self.p2]['ask'][0]['price'], r[self.p2]['ask'][0]['amount']), (r[self.p2]['bid'][0]['price'], r[self.p2]['bid'][0]['amount']))
    p3Top = ((r[self.p3]['ask'][0]['price'], r[self.p3]['ask'][0]['amount']), (r[self.p3]['bid'][0]['price'], r[self.p3]['bid'][0]['amount']))
    
    result.ask1 = p1Top[0][0]
    result.ask1_amount = p1Top[0][1]
    result.bid1 = p1Top[1][0]
    result.bid1_amount = p1Top[1][1]
    result.ask2 = p2Top[0][0]
    result.ask2_amount = p2Top[0][1]
    result.bid2 = p2Top[1][0]
    result.bid2_amount = p2Top[1][1]
    result.ask3 = p3Top[0][0]
    result.ask3_amount = p3Top[0][1]
    result.bid3 = p3Top[1][0]
    result.bid3_amount = p3Top[1][1]
    
    return result