import sys
import decimal
from decimal import Decimal
from concurrent import futures

import btceapi
import bitfinex

import arbmath
from arbmath import Order

class AbstractTradeApi(object):
  def __init__(self):
    self.orderQueue = []
  
  def Name(self):
    return ''
  
  #Fee (%)
  def Comission(self):
    return Decimal('0.0')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    pass
  
  def getSymbolList(self, pairList):
    symbolList = []
    for pair in pairList:
      symbolList = symbolList + [pair[:3]]
      symbolList = symbolList + [pair[3:]]
    symbolList = list(set(symbolList))
    return symbolList

  #returns depths for a list of pairs and balance for corresponding securities
  def GetDepths(self, pairList, askLimit = 50, bidLimit = 50, maxWorkers = 5):
    symbolList = self.getSymbolList(pairList)
    
    with futures.ThreadPoolExecutor(max_workers=maxWorkers) as executor:
      balanceFuture = executor.submit(lambda : self.GetBalance(symbolList))
      depths = dict(executor.map(lambda pair: (pair, self.GetDepth(pair, askLimit, bidLimit)), pairList))
      r = balanceFuture.result()
      return { 'depths': depths, 'balance': r }
  
  def GetBalance(self, symbolList):
    pass
  
  def PlaceOrder(self, pair, orderType, price, amount):
    #TODO
    pass
  
  def EnqueueOrder(self, pair, orderType, price, amount):
    self.orderQueue = self.orderQueue + [(pair, orderType, price, amount)]
    
  def EnqueueOrderA(self, order):
    self.EnqueueOrder(order.pair, order.orderType, order.price, order.amount)
  
  def PlacePendingOrders(self):
    pass
  
  def CancelPendingOrders(self):
    self.orderQueue = []
  
  def FormatPrice(self, pair, price):
    pass
  
  def FormatAmount(self, pair, amount):
    pass
  
  def GetMinAmount(self, pair):
    pass


class Pairs:
  btcusd = 'btcusd'
  btcltc = 'btcltc'
  ltcusd = 'ltcusd'
    
class BTCETradeApi(AbstractTradeApi):
  btcePairs = { 'btcusd':'btc_usd', 'ltcbtc':'ltc_btc', 'ltcusd':'ltc_usd', 'nmcbtc': 'nmc_btc', 'nmcusd': 'nmc_usd',\
  'ppcbtc': 'ppc_btc', 'ppcusd': 'ppc_usd', 'nvcusd': 'nvc_usd', 'nvcbtc': 'nvc_btc'}
  
  def __init__(self, keyFileList):
    super(BTCETradeApi,self).__init__()
    
    #todo check for empty list
    self.keyFileList = keyFileList
    self.handlerList = [btceapi.KeyHandler(keyFile, resaveOnDeletion=True) for keyFile in keyFileList] 
    self.tradeApiList = [btceapi.TradeAPI(keyHandler.getKeys()[0], keyHandler) for keyHandler in self.handlerList]
    self.tradeapi = self.tradeApiList[0]
  
  def Name(self):
    return "BTC-e"
  
  #Fee (%)
  def Comission(self):
    return Decimal('0.2')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    if(not pair in self.btcePairs):
      return {}
      
    asks, bids = btceapi.getDepth(self.btcePairs[pair])
    result = { \
      'ask' : [{ 'price' : price, 'amount' : amount } for price, amount in asks[:askLimit]], \
      'bid' : [{ 'price' : price, 'amount' : amount } for price, amount in bids[:bidLimit]]  \
      }
            
    return result
  
  def GetBalance(self, symbolList):
    info = self.tradeapi.getInfo()
    return { s : getattr(info, 'balance_'+s) for s in symbolList }
  
  def PlacePendingOrders(self):
    workerCount = len(self.tradeApiList)
    result = []
    while(self.orderQueue):
      ordersToPlace = self.orderQueue[:workerCount]
      self.orderQueue = self.orderQueue[workerCount:]
      orderApiCombination = zip(ordersToPlace, self.tradeApiList)
      with futures.ThreadPoolExecutor(max_workers=workerCount) as executor:
        partialResult = executor.map(lambda c: c[1].trade(self.btcePairs[c[0][0]], c[0][1], c[0][2], c[0][3]), orderApiCombination)
        for e in partialResult:
          result = result + [e]
    return result
  
  def FormatAmount(self, pair, amount):
    return btceapi.truncateAmount(amount, self.btcePairs[pair])

  def FormatPrice(self, pair, price):
    return btceapi.truncateAmount(price, self.btcePairs[pair])

  def GetMinAmount(self, pair):
    return btceapi.min_orders[self.btcePairs[pair]]
  
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  def close(self):
    for handler in self.handlerList:
      handler.close()
    
class BitfinexTradeApi(AbstractTradeApi):
  
  def __init__(self, keyfile):
    super(BitfinexTradeApi,self).__init__()
    self.tradeapi = bitfinex.Bitfinex()
  
  def Name(self):
    return "Bitfinex"
  
  def Comission(self):
    #todo
    return Decimal('0.15')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    
    r = self.tradeapi.book({ 'limit_bids' : bidLimit, 'limit_asks' : askLimit }, pair)
    #print "Get depth for symbol %s" % pair
    
    #print r
    
    result = { \
      'ask' : [{ 'price' : e[u'price'], 'amount' : e[u'amount'] } for e in r['asks']], \
      'bid' : [{ 'price' : e[u'price'], 'amount' : e[u'amount'] } for e in r['bids']]  \
      }
    
    return result

class DummyTradeResult(object):
  def __init__(self):
    self.received = Decimal('0')
 
class DummyTradeApi(AbstractTradeApi):
  btcePairs = { 'btcusd':'btc_usd', 'ltcbtc':'ltc_btc', 'ltcusd':'ltc_usd', 'nmcbtc': 'nmc_btc', 'nmcusd': 'nmc_usd',\
  'ppcbtc': 'ppc_btc', 'ppcusd': 'ppc_usd', 'nvcusd': 'nvc_usd', 'nvcbtc': 'nvc_btc'}
  
  def __init__(self, keyFileList):
    super(DummyTradeApi,self).__init__()
    
    #todo check for empty list
    self.keyFileList = keyFileList
    self.handlerList = [btceapi.KeyHandler(keyFile, resaveOnDeletion=True) for keyFile in keyFileList] 
    self.tradeApiList = [btceapi.TradeAPI(keyHandler.getKeys()[0], keyHandler) for keyHandler in self.handlerList]
    self.tradeapi = self.tradeApiList[0]
  
  def Name(self):
    return "Dummy"
  
  #Fee (%)
  def Comission(self):
    return Decimal('0.2')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    if(not pair in self.btcePairs):
      return {}
      
    asks, bids = btceapi.getDepth(self.btcePairs[pair])
    result = { \
      'ask' : [{ 'price' : (price / Decimal('2')), 'amount' : amount } for price, amount in asks[:askLimit]], \
      'bid' : [{ 'price' : price, 'amount' : amount } for price, amount in bids[:bidLimit]]  \
      }
            
    return result
  
  def GetBalance(self, symbolList):
    return { s : Decimal('100') for s in symbolList }
  
  def PlacePendingOrders(self):
    result = []
    for order in self.orderQueue:
      print "DummyTradeApi: placing order: %s" % str(order)
      result = result + [DummyTradeResult()]
    return result
  
  def FormatAmount(self, pair, amount):
    return btceapi.truncateAmount(amount, self.btcePairs[pair])

  def FormatPrice(self, pair, price):
    return btceapi.truncateAmount(price, self.btcePairs[pair])

  def GetMinAmount(self, pair):
    return btceapi.min_orders[self.btcePairs[pair]]
  
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  def close(self):
    for handler in self.handlerList:
      handler.close()
    
def CreateTradeApi(exchangeName, keyfileList):
  if exchangeName.lower() == 'btce' or exchangeName.lower() == 'btc-e':
    return BTCETradeApi(keyfileList)
  elif exchangeName.lower() == 'bitfinex':
    return BitfinexTradeApi(keyfileList[0])
  elif exchangeName.lower() == 'dummy':
    return DummyTradeApi(keyfileList)
  else:
    return None