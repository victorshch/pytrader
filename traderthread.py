import sys
import decimal
from decimal import Decimal
import PyQt4
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import pyqtSignal

import btceapi

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

class TimerRestarter(object):
  def __init__(self, timer):
    self.timer = timer
  def __enter__(self):
    return self
  def __exit__(self, type, value, traceback):
    self.timer.start()
  

class TraderThread(QtCore.QThread):
  timer = QtCore.QTimer()
  stopwatch = QtCore.QTime()
  tradeTimer = QtCore.QTimer()
  updateData = pyqtSignal(Tops, ArbData, ArbData)
  updateLag = pyqtSignal(int)
  def __init__(self, parent, tradeAPI, p1='btcusd', p2='ltcbtc', p3 = 'ltcusd', refreshInterval=100, tradeInterval=15000,
  s1ToSpend = 20, s2ToSpend = 0.03, s3ToSpend = 4, minProfit = 0.01, maxLag = 900):
    super(TraderThread, self).__init__(parent)
    self.tradeAPI = tradeAPI
    self.k = Decimal('1') - (tradeAPI.Comission() / Decimal('100.0'))
    self.p1 = p1
    self.p2 = p2
    self.p3 = p3
    self.s1 = p1[3:]
    self.s2 = p1[:3]
    self.s3 = p3[:3]
    self.minProfit = minProfit
    self.maxLag = maxLag
    self.s1ToSpend = s1ToSpend
    self.s2ToSpend = s2ToSpend
    self.s3ToSpend = s3ToSpend
    self.balance = {}
    self.remainders = {}
    self.timer.setInterval(refreshInterval)
    self.timer.setSingleShot(True)
    self.tradeTimer.setInterval(tradeInterval)
    self.tradeTimer.setSingleShot(True)
    self.timer.timeout.connect(self.onTimer)

  @pyqtSlot()
  def onTimer(self):
    with TimerRestarter(self.timer) as timerRestarter:
      self.stopwatch.start()
      t = self.GetTops()
      self.tops = t
      elapsed = self.stopwatch.elapsed()
      self.lag = elapsed
      self.updateLag.emit(elapsed)
      
      a1, b1 = t.ask1, t.bid1
      a2, b2 = t.ask2, t.bid2
      a3, b3 = t.ask3, t.bid3
      
      k3 = self.k * self.k * self.k
      
      profit1 = k3 * (b3) / ((a1) * (a2)) - Decimal('1.0')
      profit2 = k3 * (b1) * (b2) / (a3)  - Decimal('1.0')
      
      if profit1 > 0:
        self.tradeForward()
      elif profit2 > 0:
        self.tradeBackward()
      
      a1 = ArbData("Forward", profit1)
      a2 = ArbData("Backward", profit2)

      self.updateData.emit(t, a1, a2)

  def tradeForward(self):
    a1, X, b1, X2 = self.tops.ask1, self.tops.ask1_amount, self.tops.bid1, self.tops.bid1_amount
    a2, Y, b2, Y2 = self.tops.ask2, self.tops.ask2_amount, self.tops.bid2, self.tops.bid2_amount
    a3, Z2, b3, Z = self.tops.ask3, self.tops.ask3_amount, self.tops.bid3, self.tops.bid3_amount
    
    print "%s: exploring %s->%s->%s->%s arbitrage opportunity" % (str(QtCore.QDateTime.currentDateTime().toString()), self.s1, self.s2, self.s3, self.s1)
    
    k = self.k
    k2 = self.k * self.k
    k3 = k2 * self.k
    
    s1 = self.s1
    s2 = self.s2
    s3 = self.s3
    p1 = self.p1
    p2 = self.p2
    p3 = self.p3
    
    usdToSpend = min(self.balance[s1], self.s1ToSpend, a1 / k * min(X, self.s2ToSpend, self.balance[s2]), a1 * a2 / k2 * min(Y, self.s3ToSpend, self.balance[s3]), a1 * a2 / k3 * Z)
    
    profit1 = k3 * b3 / (a1 * a2) - Decimal('1.0')
    
    usdProfit = usdToSpend * profit1
    if(usdProfit < self.minProfit):
      print "Investment " + str(usdToSpend) + ", profit " + str(usdProfit) + " less than " + str(self.minProfit)
      return False
      
    btcToBuy = self.tradeAPI.FormatAmount(p1, k * usdToSpend / a1)
    ltcToBuy = self.tradeAPI.FormatAmount(p2, k * btcToBuy / a2)
    
    if btcToBuy < btceapi.min_orders[p1]:
      print "%s to buy %s less than minimum %s" %(s2, btcToBuy, btceapi.min_orders[p2])
      return False
      
    if ltcToBuy < btceapi.min_orders[p2]:
      print "%s to buy %s less than minimum %s" %(s3, ltcToBuy, btceapi.min_orders[p3])
      return False
    
    if self.lag > self.maxLag:
      print "Lag %s is greater than maximum lag %s, not trading" % (self.lag, self.maxLag)
      return False
    
    if not self.tradeTimer.isActive():
      print "Buying %s %s at price %s %s" % (btcToBuy, s2, a1, s1)
      
      self.tradeAPI.EnqueueOrder(p1, "buy", a1, btcToBuy)
      
      print "Buying %s %s at price %s %s" % (ltcToBuy, s3, a2, s2)
      
      self.tradeAPI.EnqueueOrder(p2, "buy", a2, ltcToBuy)
      
      print "Selling %s %s at price %s %s" % (ltcToBuy, s3, b3, s1)
      
      self.tradeAPI.EnqueueOrder(p3, "sell", b3, ltcToBuy)
      
      print "Executing orders..."
      
      result = self.tradeAPI.PlacePendingOrders()
      
      print "Trade 1, received: " + str(result[0].received)
      print "Trade 2, received: " + str(result[1].received)
      print "Trade 3, received: " + str(result[2].received)
      
      return True
    else:
      print "Trade timer is active, not trading"
      
      return False
  def tradeBackward(self):
    a1, X, b1, X2 = self.tops.ask1, self.tops.ask1_amount, self.tops.bid1, self.tops.bid1_amount
    a2, Y, b2, Y2 = self.tops.ask2, self.tops.ask2_amount, self.tops.bid2, self.tops.bid2_amount
    a3, Z2, b3, Z = self.tops.ask3, self.tops.ask3_amount, self.tops.bid3, self.tops.bid3_amount
    
    print "%s: exploring %s->%s->%s->%s arbitrage opportunity" % (str(QtCore.QDateTime.currentDateTime().toString()), self.s1, self.s3, self.s2, self.s1)
    
    k = self.k
    k2 = self.k * self.k
    k3 = k2 * self.k
    
    s1 = self.s1
    s2 = self.s2
    s3 = self.s3
    p1 = self.p1
    p2 = self.p2
    p3 = self.p3
    
    usdToSpend = min(self.s1ToSpend, self.balance[s1], a3 / k * min(Z, self.s3ToSpend, self.balance[s3]), a3 / (k2 * b2) * min(float(int(Y * b2 * 100))/100, self.s2ToSpend, self.balance[s2]), X * a3 / (k3 * b2))
    
    profit2 = k3 * float(b1) * float(b2) / float(a3) - 1.0

    usdProfit = usdToSpend * profit2
    if(usdProfit < self.minProfit):
      print "Investment " + str(usdToSpend) + ", profit " + str(usdProfit) + " less than " + str(self.minProfit)
      return False
      
    ltcToBuy = self.tradeAPI.FormatAmount(p3, k * usdToSpend / a3)
    btcToBuy = self.tradeAPI.FormatAmount(p1, k * ltcToBuy * b2)
    ltcToBuy = self.tradeAPI.FormatAmount(p3, btcToBuy / (k * b2))
    usdToGain = k * btcToBuy * b1
    
    if btcToBuy < btceapi.min_orders[p1]:
      print "%s to buy " % s2 + str(btcToBuy) + " less than minimum " + str(btceapi.min_orders[p2])
      return
      
    if ltcToBuy < btceapi.min_orders[p2]:
      print "%s to buy " %s3 + str(ltcToBuy) + " less than minimum " + str(btceapi.min_orders[p3])
      return
      
    if self.lag > self.maxLag:
      print "Lag %s is greater than maximum lag %s, not trading" % (self.lag, self.maxLag)
      return False
    
    if not self.tradeTimer.isActive():
      print "Buying " + str(ltcToBuy) + " ltc at price " + str(a3) + " usd"
      
      self.tradeAPI.EnqueueOrder(p3, "buy", a3, ltcToBuy)
      
      print "Selling " + str(ltcToBuy) + " ltc at price " + str(b2) + " btc"
      
      self.tradeAPI.EnqueueOrder(p2, "sell", b2, ltcToBuy)
      
      print "Selling " + str(btcToBuy) + " btc at price " + str(b1) + " usd"
      
      self.tradeAPI.EnqueueOrder(p1, "sell", b1, btcToBuy)
      
      print "Executing orders..."
      result1, result2, result3 = self.tradeAPI.PlacePendingOrders()
      
      print "Trade 1, received: " + str(result1.received)
      print "Trade 2, received: " + str(result2.received)
      print "Trade 3, received: " + str(result3.received)
    else:
      print "Trade timer is active, not trading"

  def run(self):
    self.timer.start()
    self.exec_()
  
  def GetTop(self, pair):
    r = self.tradeAPI.GetDepth(pair, 1, 1)
    return ((r['ask'][0]['price'], r['ask'][0]['amount']), (r['bid'][0]['price'], r['bid'][0]['amount']))
  
  def GetTops(self):
    result = Tops()
    depthsAndBalance  = self.tradeAPI.GetDepths([self.p1, self.p2, self.p3], 1, 1, 5)
    r = depthsAndBalance['depths']
    self.balance = depthsAndBalance['balance']
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