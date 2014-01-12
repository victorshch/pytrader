import sys
import decimal
from decimal import Decimal

import btceapi
import bitfinex


class AbstractTradeApi(object):
  def __init__(self):
    self.orderQueue = []
    
  #Fee (%)
  def Comission(self):
    return Decimal('0.0')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    pass
  
  def QueueOrder(self, pair, orderType, price, amount):
    #TODO
    pass
  
  def PlacePendingOrders(self):
    #TODO
    pass

class Pairs:
  btcusd = 'btcusd'
  btcltc = 'btcltc'
  ltcusd = 'ltcusd'
    
class BTCETradeApi(AbstractTradeApi):
  btcePairs = { 'btcusd':'btc_usd', 'ltcbtc':'ltc_btc', 'ltcusd':'ltc_usd' }
  
  def __init__(self, key_file, nonce=1):
    self.key_file = key_file
    self.handler = btceapi.KeyHandler(key_file, resaveOnDeletion=True)
    key = self.handler.getKeys()[0]
    self.tradeapi = btceapi.TradeAPI(key, handler=self.handler)
  
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
  
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  def close():
    self.handler.close()
    
class BitfinexTradeApi(AbstractTradeApi):
  
  def __init__(self):
    self.tradeapi = bitfinex.Bitfinex()
    
  def Comission(self):
    #todo
    return Decimal('0.15')
  
  def GetDepth(self, pair, askLimit = 50, bidLimit = 50):
    
    r = self.tradeapi.book({ 'limit_bids' : bidLimit, 'limit_asks' : askLimit }, pair)
    #print "Get depth for symbol %s" % pair
    
    #print r
    
    result = { \
      'ask' : [{ 'price' : e[u'price'], 'amount' : e[u'amount'] } for e in r[u'asks']], \
      'bid' : [{ 'price' : e[u'price'], 'amount' : e[u'amount'] } for e in r[u'bids']]  \
      }
    
    return result