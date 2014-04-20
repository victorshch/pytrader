import sys
import decimal
from decimal import Decimal
import copy
import PyQt4
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import pyqtSignal
import arbmath
from arbmath import Order

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
  def __init__(self, direction = "Forward", p = Decimal('0'), usdProfit = Decimal('0'), usdInvestment = Decimal('0')):
    self.tradeDirection = direction
    self.profit = p
    self.usdProfit = usdProfit
    self.usdInvestment = usdInvestment
  
class Balance(object):
  balance_usd = Decimal('0')
  balance_ltc = Decimal('0')
  balance_btc = Decimal('0')

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
  s1ToSpend = 20, s2ToSpend = 0.03, s3ToSpend = 4, minProfit = 0.01, maxLag = 900, greedyPercent = Decimal('0')):
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
    self.greedyPercent = greedyPercent
    self.greedyMultiplier = Decimal('1') - greedyPercent / Decimal('100')
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
      
      balance = { self.s1: min(self.balance[self.s1], self.s1ToSpend), \
        self.s2: min(self.balance[self.s2], self.s2ToSpend), \
        self.s3: min(self.balance[self.s3], self.s3ToSpend) }
      
      orders, maxDepth = arbmath.CalculateArbOrders(self.depths, self.p1, self.p2, self.p3, self.k, balance, self.tradeAPI)
      
      usdProfit = Decimal('0.0')
      
      if orders:
        print "%s: Exploring arbitrage opportunity: %s" % (str(QtCore.QDateTime.currentDateTime().toString()), orders)
        
        if self.greedyPercent > Decimal('0'):
          for i in range(0, len(orders)):
            if orders[i].pair == self.s1:
              order = orders[i]
              if order.orderType == 'buy':
                print "Applying reducing greedy percent to price %s" % order.price
                orders[i] = Order(order.pair, order.orderType, self.tradeAPI.FormatPrice(order.pair, order.price * self.greedyMultiplier), order.amount)
                print "Result: %s" % orders[i].price
              elif order[1] == 'sell':
                print "Applying increasing greedy percent to price %s" % order.price
                orders[i] = Order(order.pair, order.orderType, self.tradeAPI.FormatPrice(order.pair, order.price / self.greedyMultiplier), order.amount)
                print "Result: %s" % orders[i].price

        exchangeModel = arbmath.ExchangeModel(self.depths, self.tradeAPI)
        
        newBalance = copy.deepcopy(balance)
        for order in orders:
          newBalance, pendingOrder = exchangeModel.ModelTrade(newBalance, order.pair, order.orderType, order.price, order.amount)
        
        usdProfit = newBalance[self.s1] - balance[self.s1]
        
        print "Profit: %s" % usdProfit
        
        s2Change = newBalance[self.s2] - balance[self.s2]
        if s2Change > 0:
          usdProfit += s2Change * b1
        else:
          usdProfit += s2Change * a1
          
        s3Change = newBalance[self.s3] - balance[self.s3]
        if s3Change > 0:
          usdProfit += s3Change * b3
        else:
          usdProfit += s3Change * a3
        
        print "%s gain: %s" % (self.s2, s2Change)
        print "%s gain: %s" % (self.s3, s3Change)
        
        print "Overall profit: %s" % usdProfit
        
        if not self.tradeTimer.isActive():
          if usdProfit > self.minProfit:
            self.tradeAPI.EnqueueOrderA(order)
            
            print "Placing orders..."
            r1, r2, r3 = self.tradeAPI.PlacePendingOrders()
            
            print "Received from trade 1: %s" % r1.received
            print "Received from trade 2: %s" % r2.received
            print "Received from trade 3: %s" % r3.received
            
            self.tradeTimer.start()
          else:
            print "Profit %s less than min profit %s" % (usdProfit, self.minProfit)
        else:
          print "Trade timer is active, not trading"
          
      a1 = ArbData("Forward", profit1, usdProfit)
      a2 = ArbData("Backward", profit2, usdProfit)

      self.updateData.emit(t, a1, a2)

  def run(self):
    self.timer.start()
    self.exec_()
  
  def GetTop(self, pair):
    r = self.tradeAPI.GetDepth(pair, 1, 1)
    return ((r['ask'][0]['price'], r['ask'][0]['amount']), (r['bid'][0]['price'], r['bid'][0]['amount']))
  
  def GetTops(self):
    result = Tops()
    depthsAndBalance  = self.tradeAPI.GetDepths([self.p1, self.p2, self.p3], 50, 50, 5)
    r = depthsAndBalance['depths']
    self.balance = depthsAndBalance['balance']
    p1Top = ((r[self.p1]['ask'][0]['price'], r[self.p1]['ask'][0]['amount']), (r[self.p1]['bid'][0]['price'], r[self.p1]['bid'][0]['amount']))
    p2Top = ((r[self.p2]['ask'][0]['price'], r[self.p2]['ask'][0]['amount']), (r[self.p2]['bid'][0]['price'], r[self.p2]['bid'][0]['amount']))
    p3Top = ((r[self.p3]['ask'][0]['price'], r[self.p3]['ask'][0]['amount']), (r[self.p3]['bid'][0]['price'], r[self.p3]['bid'][0]['amount']))
    
    self.depths = r
    
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