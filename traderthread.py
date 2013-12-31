import sys
import PySide

refreshInterval = 100
tradeInterval = 15000

p1 = "btc_usd"
p2 = "ltc_btc"
p3 = "ltc_usd"

def getTopOfTheBook(symbol):
  asks, bids = btceapi.getDepth(symbol)
  return (float(asks[0][0]), float(asks[0][1]), float(bids[0][0]), float(bids[0][1]))
  
def getTopOfTheBook2(symbol):
  asks, bids = btceapi.getDepth(symbol)
  return (float(asks[1][0]), float(asks[0][1] + asks[1][1]), float(bids[1][0]), float(bids[0][1] + bids[1][1]))
  
def getTopOfTheBook3(symbol):
  asks, bids = btceapi.getDepth(symbol)
  return (float(asks[2][0]), float(asks[0][1] + asks[1][1] + asks[2][1]), float(bids[2][0]), float(bids[0][1] + bids[1][1] + bids[2][1]))

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


class Tops(object):
  ask1 = 0
  ask1_amount = 0
  bid1 = 0
  bid1_amount = 0
  ask2 = 0
  ask2_amount = 0
  bid2 = 0
  bid2_amount = 0
  ask3 = 0
  ask3_amount = 0
  bid3 = 0
  bid3_amount = 0
  
class ArbData(object):
  tradeDirection = "Forward"
  profit = 0
  usdProfit = 0
  usdInvestment = 0
  
class Balance(object):
  balance_usd = 0
  balance_ltc = 0
  balance_btc = 0

class TraderThread(QtCore.QThread):
  timer = QtCore.QTimer()
  tradeTimer = QtCore.QTimer()
  def __init_(self, tradeAPI):
    self.tradeAPI = tradeAPI
    self.timer.setInterval(refreshInterval)
    self.timer.setSingleShot(0)
    self.tradeTimer.setInterval(tradeInterval)
    self.tradeTimer.setSingleShot(1)
    self.updateData = QtCore.QSignal(QtCore.QDateTime, Tops, ArbData, Balance)
    
  def run():
    pass
    #todo
    
  #todo
  
  