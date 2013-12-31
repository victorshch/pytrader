import sys
import PySide
import ui_mainwindow
from PySide import QtGui
from PySide import QtCore
import btceapi

epsilon = 0.0000001


def getTopOfTheBook(symbol):
  asks, bids = btceapi.getDepth(symbol)
  #return (float(asks[1][0]), float(asks[0][1] + asks[1][1]), float(bids[1][0]), float(bids[0][1] + bids[1][1]))
  return (float(asks[0][0]), float(asks[0][1]), float(bids[0][0]), float(bids[0][1]))
  
def getTopOfTheBook2(symbol):
  asks, bids = btceapi.getDepth(symbol)
  return (float(asks[1][0]), float(asks[0][1] + asks[1][1]), float(bids[1][0]), float(bids[0][1] + bids[1][1]))
  
def getTopOfTheBook3(symbol):
  asks, bids = btceapi.getDepth(symbol)
  return (float(asks[2][0]), float(asks[0][1] + asks[1][1] + asks[2][1]), float(bids[2][0]), float(bids[0][1] + bids[1][1] + bids[2][1]))

def getTopOfTheBookMinSum(symbol, s):
  asks, bids = btceapi.getDepth(symbol)
  askDepth = 0
  bidDepth = 0
  ask, askAmount, bid, bidAmount = float(asks[0][0]), float(asks[0][1]), float(bids[0][0]), float(bids[0][1])
  askSum = ask * askAmount
  bidSum = bid * bidAmount
  while(askSum < s):
    askDepth = askDepth + 1
    askSum = askSum + float(asks[askDepth][0]) * float(asks[askDepth][1])
    ask = float(asks[askDepth][0])
    askAmount = askAmount + float(asks[askDepth][1])
  while(bidSum < s):
    bidDepth = bidDepth + 1
    bidSum = bidSum + float(bids[bidDepth][0]) * float(bids[bidDepth][1])
    bid = float(bids[bidDepth][0])
    bidAmount = bidAmount + float(bids[bidDepth][1])
  return ask, askAmount, bid, bidAmount
  
def getTopOfTheBookMinAmount(symbol, minAskAmount, minBidAmount):
  asks, bids = btceapi.getDepth(symbol)
  askDepth = 0
  bidDepth = 0
  ask, askAmount, bid, bidAmount = float(asks[0][0]), float(asks[0][1]), float(bids[0][0]), float(bids[0][1])
  while(askAmount < minAskAmount):
    askDepth = askDepth + 1
    ask = float(asks[askDepth][0])
    askAmount = askAmount + float(asks[askDepth][1])
  while(bidAmount < minBidAmount):
    bidDepth = bidDepth + 1
    bid = float(bids[bidDepth][0])
    bidAmount = bidAmount + float(bids[bidDepth][1])
  return ask, askAmount, bid, bidAmount

  
def refreshPairData(top, spinBox1, spinBox2, spinBox3, spinBox4):
  spinBox1.setValue(top[0])
  spinBox2.setValue(top[2])
  spinBox3.setValue(top[1])
  spinBox4.setValue(top[3])
  return

p1 = "btc_usd"
p2 = "ltc_btc"
p3 = "ltc_usd"

def formatBTC(amount):
  return float(int(amount*100))/100

tradeTimeout = 10000

k = float(0.998)
k2 = k * k
k3 = k * k * k
maxUSD = 50.0
maxBTC = 0.1
maxLTC = 3.0

minProfit = 0.01

tradeTimer = QtCore.QTimer()
tradeTimer.setInterval(tradeTimeout)
tradeTimer.setSingleShot(1)

class Listener(QtCore.QObject):
  maxProfit = float(-1.0)
  top1 = (1, 1, 1, 1)
  top2 = (1, 1, 1, 1)
  top3 = (1, 1, 1, 1)
  def __init__(self, itemModel, timer, tradeAPI):
    self.itemModel = itemModel
    self.timer = timer
    self.tradeAPI = tradeAPI
    self.balance_usd = 0
    self.balance_btc = 0
    self.balance_ltc = 0
  #def confirmTop(self):
    #t1 = getTopOfTheBook(p1);
    #t2 = getTopOfTheBook3(p2);
    #t3 = getTopOfTheBook2(p3);
    
    #info = tradeAPI.getInfo()
    #balance_usd = info.balance_usd
    #balance_ltc = info.balance_ltc
    #balance_btc = info.balance_btc
    
    #print ("top1: " + str(self.top1) + ", t1: " + str(t1) + "\n"
      #+"top1: " + str(self.top2) + ", t1: " + str(t2) + "\n"
      #"top1: " + str(self.top3) + ", t1: " + str(t3))
    #return (abs(t1[0] - self.top1[0]) < epsilon and 
      #abs(t1[1] - self.top1[1]) < epsilon and 
      #abs(t1[2] - self.top1[2]) < epsilon and
      #abs(t1[3] - self.top1[3]) < epsilon and
      #abs(t2[0] - self.top2[0]) < epsilon and
      #abs(t2[1] - self.top2[1]) < epsilon and
      #abs(t2[2] - self.top2[2]) < epsilon and
      #abs(t2[3] - self.top2[3]) < epsilon and
      #abs(t3[0] - self.top3[0]) < epsilon and
      #abs(t3[1] - self.top3[1]) < epsilon and
      #abs(t3[2] - self.top3[2]) < epsilon and
      #abs(t3[3] - self.top3[3]) < epsilon)
    
  def tradeForward(self):
    #if(not self.confirmTop()):
      #print "Failed to confirm top"
      #return
    a1, X, b1, X2 = self.top1
    a2, Y, b2, Y2 = self.top2
    a3, Z2, b3, Z = self.top3
    
    print str(QtCore.QDateTime.currentDateTime().toString()) + ": exploring usd->btc->ltc->usd arbitrage opportunity"
    
    usdToSpend = min(self.balance_usd, maxUSD, a1 / k * min(X, maxBTC, self.balance_btc), a1 * a2 / k2 * min(Y, maxLTC, self.balance_ltc), a1 * a2 / k3 * Z)
    
    profit1 = k3 * float(b3) / (float(a1) * float(a2)) - 1.0
    
    usdProfit = usdToSpend * profit1
    if(usdProfit < minProfit):
      print "Investment " + str(usdToSpend) + ", profit " + str(usdProfit) + " less than " + str(minProfit)
      return
      
    btcToBuy = formatBTC(k * usdToSpend / a1)
    ltcToBuy = k * btcToBuy / a2
    
    if btcToBuy < btceapi.min_orders[p1]:
      print "BTC to buy " + str(btcToBuy) + " less than minimum " + str(btceapi.min_orders[p1])
      return
      
    if ltcToBuy < btceapi.min_orders[p2]:
      print "LTC to buy " + str(ltcToBuy) + " less than minimum " + str(btceapi.min_orders[p2])
      return
    
    if not tradeTimer.isActive():
      print "Buying " + str(btcToBuy) + " btc at price " + str(a1) + " usd"
      
      result1 = tradeAPI.trade(p1, "buy", a1, btcToBuy)
      
      print "Trade 1, received: " + str(result1.received)
      print "Buying " + str(ltcToBuy) + " ltc at price " + str(a2) + " btc"
      
      result2 = tradeAPI.trade(p2, "buy", a2, ltcToBuy)
      
      print "Trade 2, received: " + str(result2.received)
      print "Selling " + str(ltcToBuy) + " ltc at price " + str(b3) + " usd"
      
      result3 = tradeAPI.trade(p3, "sell", b3, ltcToBuy)
      
      print "Trade 3, received: " + str(result3.received)
    else:
      print "Trade timer is active, not trading"
    
    lastItem = QtGui.QStandardItem()
    lastItem.setText(str(usdProfit))
    lastItem.setToolTip(str(usdToSpend))
    
    model.appendRow([QtGui.QStandardItem(str(QtCore.QDateTime.currentDateTime().toString())),
      QtGui.QStandardItem("Forward"),
      QtGui.QStandardItem(str(a1)),
      QtGui.QStandardItem(str(X)),
      QtGui.QStandardItem(str(b1)),
      QtGui.QStandardItem(str(X2)),
      QtGui.QStandardItem(str(a2)),
      QtGui.QStandardItem(str(Y)),
      QtGui.QStandardItem(str(b2)),
      QtGui.QStandardItem(str(Y2)),
      QtGui.QStandardItem(str(a3)),
      QtGui.QStandardItem(str(Z2)),
      QtGui.QStandardItem(str(b3)),
      QtGui.QStandardItem(str(Z)),
      QtGui.QStandardItem(str(profit1 * 100) + "%"),
      lastItem])
    model.reset()
    
  def tradeBackward(self):
    #if(not self.confirmTop()):
      #print "Failed to confirm top"
      #return
    a1, X2, b1, X = self.top1
    a2, Y2, b2, Y = self.top2
    a3, Z, b3, Z2 = self.top3
    
    print str(QtCore.QDateTime.currentDateTime().toString()) + ": exploring usd->ltc->btc->usd arbitrage opportunity"
    
    usdToSpend = min(maxUSD, self.balance_usd, a3 / k * min(Z, maxLTC, self.balance_ltc), a3 / (k2 * b2) * min(float(int(Y * b2 * 100))/100, maxBTC, self.balance_btc), X * a3 / (k3 * b2))
    
    profit2 = k3 * float(b1) * float(b2) / float(a3) - 1.0

    usdProfit = usdToSpend * profit2
    if(usdProfit < minProfit):
      print "Investment " + str(usdToSpend) + ", profit " + str(usdProfit) + " less than " + str(minProfit)
      return
      
    ltcToBuy = k * usdToSpend / a3
    btcToBuy = formatBTC(k * ltcToBuy * b2)
    ltcToBuy = btcToBuy / (k * b2)
    usdToGain = k * btcToBuy * b1
    
    print "usdToSpend: " + str(usdToSpend) + ", usdToGain: " + str(usdToGain)
    print "ltcToBuy: " + str(ltcToBuy)
    print "btcToBuy: " + str(btcToBuy)
    
    if btcToBuy < btceapi.min_orders[p1]:
      print "BTC to buy " + str(btcToBuy) + " less than minimum " + str(btceapi.min_orders[p1])
      return
      
    if ltcToBuy < btceapi.min_orders[p2]:
      print "LTC to buy " + str(ltcToBuy) + " less than minimum " + str(btceapi.min_orders[p2])
      return
    
    if not tradeTimer.isActive():
      print "Buying " + str(ltcToBuy) + " ltc at price " + str(a3) + " usd"
      
      result1 = tradeAPI.trade(p3, "buy", a3, ltcToBuy)
      
      print "Trade 1, received: " + str(result1.received)
      print "Selling " + str(ltcToBuy) + " ltc at price " + str(b2) + " btc"
      
      result2 = tradeAPI.trade(p2, "sell", b2, ltcToBuy)
      
      print "Trade 2, received: " + str(result2.received)
      print "Selling " + str(btcToBuy) + " btc at price " + str(b1) + " usd"
      
      result3 = tradeAPI.trade(p1, "sell", b1, btcToBuy)
      
      print "Trade 3, received: " + str(result3.received)
    else:
      print "Trade timer is active, not trading"
    
    lastItem = QtGui.QStandardItem()
    lastItem.setText(str(usdProfit))
    lastItem.setToolTip(str(usdToSpend))

    model.appendRow([QtGui.QStandardItem(str(QtCore.QDateTime.currentDateTime().toString())),
      QtGui.QStandardItem("Backward"),
      QtGui.QStandardItem(str(a1)),
      QtGui.QStandardItem(str(X2)),
      QtGui.QStandardItem(str(b1)),
      QtGui.QStandardItem(str(X)),
      QtGui.QStandardItem(str(a2)),
      QtGui.QStandardItem(str(Y2)),
      QtGui.QStandardItem(str(b2)),
      QtGui.QStandardItem(str(Y)),
      QtGui.QStandardItem(str(a3)),
      QtGui.QStandardItem(str(Z)),
      QtGui.QStandardItem(str(b3)),
      QtGui.QStandardItem(str(Z2)),
      QtGui.QStandardItem(str(profit2 * 100) + "%"),
      lastItem])
    model.reset()

  @QtCore.Slot()
  def onTimer(self):
    
    info = tradeAPI.getInfo()
    self.balance_usd = float(info.balance_usd)
    self.balance_btc = float(info.balance_btc)
    self.balance_ltc = float(info.balance_ltc)
    
    self.top1 = getTopOfTheBook(p1)
    self.top2 = getTopOfTheBook(p2)
    self.top3 = getTopOfTheBookMinAmount(p3, float(btceapi.min_orders[p1])/self.top2[0], float(btceapi.min_orders[p1])/self.top2[2])
    a1, b1 = self.top1[0], self.top1[2]
    a2, b2 = self.top2[0], self.top2[2]
    a3, b3 = self.top3[0], self.top3[2]
    refreshPairData(self.top1, content.doubleSpinBox_sec1_ask, content.doubleSpinBox_sec1_bid,
      content.doubleSpinBox_sec1_askAmount, content.doubleSpinBox_sec1_bidAmount)
    refreshPairData(self.top2, content.doubleSpinBox_sec2_ask, content.doubleSpinBox_sec2_bid,
      content.doubleSpinBox_sec2_askAmount, content.doubleSpinBox_sec2_bidAmount)
    refreshPairData(self.top3, content.doubleSpinBox_sec3_ask, content.doubleSpinBox_sec3_bid,
      content.doubleSpinBox_sec3_askAmount, content.doubleSpinBox_sec3_bidAmount)
    profit1 = k3 * float(b3) / (float(a1) * float(a2))  - 1.0
    profit2 = k3 * float(b1) * float(b2) / float(a3)  - 1.0
    if profit1 > 0:
      self.tradeForward()
    elif profit2 > 0:
      self.tradeBackward()
    self.maxProfit = max(self.maxProfit, profit1, profit2)
    content.label_result.setText('profit1 = ' + str(profit1 * 100) + '%\nprofit2 = ' + str(profit2 * 100) + '%\n' + "maxProfit = " + str(self.maxProfit * 100) + "%")
  @QtCore.Slot()
  def toggleTimer(self):
    if timer.isActive():
      timer.stop()
    else:
      timer.start()


app = QtGui.QApplication(sys.argv)
 
win = QtGui.QMainWindow()

content = ui_mainwindow.Ui_MainWindow()
content.setupUi(win)

content.label_sec1.setText(p1)
content.label_sec2.setText(p2)
content.label_sec3.setText(p3)

timer = QtCore.QTimer()
timer.setInterval(100)
timer.setSingleShot(0)

model = QtGui.QStandardItemModel()
model.setHorizontalHeaderLabels(["Time",
      "TradeDirection",
      "Ask1",
      "Ask1 amount",
      "Bid1",
      "Bid1 amount",
      "Ask2",
      "Ask2 amount",
      "Bid2",
      "Bid2 amount",
      "Ask3",
      "Ask3 amount",
      "Bid3",
      "Bid3 amount",
      "ProfitPercent",
      "USD profit"])
     
key_file = "keyfile.txt"
with btceapi.KeyHandler(key_file, resaveOnDeletion=True) as handler:
  key = handler.getKeys()[0]
  tradeAPI = btceapi.TradeAPI(key, handler=handler)
  listener = Listener(model, timer, tradeAPI)

  content.tableView_history.setModel(model)
  content.tableView_history.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
  content.pushButton_pause.clicked.connect(listener.toggleTimer)

  timer.timeout.connect(listener.onTimer)
  timer.start()

  win.show() 
  sys.exit(app.exec_())
