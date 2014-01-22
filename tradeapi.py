import sys
import decimal
from decimal import Decimal
from concurrent import futures

import btceapi
import bitfinex

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
  
  def GetDepths(self, pairList, askLimit = 50, bidLimit = 50, maxWorkers = 5):
    with futures.ThreadPoolExecutor(max_workers=maxWorkers) as executor:
      return dict(executor.map(lambda pair: (pair, self.GetDepth(pair, askLimit, bidLimit)), pairList))
  
  def GetBalance(self, symbolList):
    pass
  
  def PlaceOrder(self, pair, orderType, price, amount):
    #TODO
    pass


class Pairs:
  btcusd = 'btcusd'
  btcltc = 'btcltc'
  ltcusd = 'ltcusd'
    
class BTCETradeApi(AbstractTradeApi):
  btcePairs = { 'btcusd':'btc_usd', 'ltcbtc':'ltc_btc', 'ltcusd':'ltc_usd' }
  
  def __init__(self, key_file):
    self.key_file = key_file
    self.handler = btceapi.KeyHandler(key_file, resaveOnDeletion=True)
    key = self.handler.getKeys()[0]
    self.tradeapi = btceapi.TradeAPI(key, handler=self.handler)
  
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
    info = btceapi.getInfo()
    return { s : getattr(info, 'balance_'+s) for s in symbolList }
  
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  def close():
    self.handler.close()
    
class BitfinexTradeApi(AbstractTradeApi):
  
  def __init__(self, keyfile):
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
    
def CreateTradeApi(exchangeName, keyfile):
  if exchangeName.lower() == 'btce' or exchangeName.lower() == 'btc-e':
    return BTCETradeApi(keyfile)
  elif exchangeName.lower() == 'bitfinex':
    return BitfinexTradeApi(keyfile)
  else:
    return None