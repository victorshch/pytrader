import decimal
from decimal import Decimal

class ExchangeModel(object);
  def __init__(self, depths, tradeApi):
    self.depths = depths;
    self.tradeApi = tradeApi
    self.symbols = [key[:3] for key, value in depths] + [key[3:] for key, value in depths]
    self.symbols = list(set(self.symbols))
  
  # returns (balance, remaining order)
  def ModelL1Trade(balance, pair, type, price, amount):
    depth = self.depths[pair]
    remainingOrder = { 'pair': pair, 'type': type, 'price': price, 'amount': amount }
    remainder = remainingOrder['amount']
    traded = False
    if type == 'buy':
      if(not depth['ask']):
        return (balance, remainingOrder, traded)
      
      ask = depth['ask'][0]
      if ask['price'] > price:
        return (balance, remainingOrder, traded)
      
      tradedAmount = min(amount, ask['amount'])
      remainder = max(amount - ask['amount'], 0)
      
      ask['amount'] -= tradedAmount
      balance[pair[:3]] += tradedAmount * k
      balance[pair[3:]] -= tradedAmount * ask['price']
      traded = True
      
      if ask['amount'] == Decimal('0'):
        self.depths[pair]['ask'] = self.depths[pair]['ask'][1:]
    
    elif type == 'sell':
      if not depth['bid']:
        return (balance, remainingOrder, traded)
      
      bid = depth['bid'][0]
      if bid['price'] < price:
        return (balance, remainingOrder, traded)
      
      tradedAmount = min(amount, bid['amount'])
      remainder = max(amount - bid['amount'], 0)
      
      bid['amount'] -= tradedAmount
      balance[pair[:3]] -= tradedAmount
      balance[pair[3:]] += tradedAmount * bid['price'] * k
      traded = True
      
      if bid['amount'] == Decimal('0'):
        self.depths[pair]['bid'] = self.depths[pair]['bid'][1:]
    
    remainingOrder['amount'] = remainder
    return (balance, remainingOrder, traded)
      
  
  def ModelTrade(balance, pair, type, price, amount):
    if not (pair in depths):
      return None
    
    depth = depths[pair]
    
    if type == 'buy':
      ask = depth['ask']
      

def CalculateArb(direction, price1, price2, price3, k):
  
def CalculateElemArb(direction, books, pair1, pair2, pair3, tradeApi, balance):
  
  
# returns (list of orders that produces immediate profit, balance)
def CalculateArb(books, pair1, pair2, pair3, maxArbDepth, tradeApi, balance):
  k = 