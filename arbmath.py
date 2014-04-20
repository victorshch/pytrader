import decimal
from decimal import Decimal
import copy

class Order(object):
  def __init__(self, pair, op, price, amount):
    self.pair = pair
    self.orderType = op
    self.price = price
    self.amount = amount
  def __repr__(self):
    return "%s %s in %s at %s" % (self.orderType, self.amount, self.pair, self.price)
  def __str__(self):
    return self.__repr__()


class ExchangeModel(object):
  def __init__(self, depths, tradeApi):
    self.depths = depths;
    self.tradeApi = tradeApi
    self.symbols = [key[:3] for key in depths.keys()] + [key[3:] for key in depths.keys()]
    self.symbols = list(set(self.symbols))
  
  # returns (balance, remaining order)
  def ModelL1Trade(self, balance, pair, type, price, amount):
    
    #print "ModelL1Trade: %s %s in %s for %s" % (type, amount, pair, price)
    
    depth = self.depths[pair]
    
    #print "Depth: %s" % depth
    
    k = Decimal('1') - self.tradeApi.Comission() / Decimal('100')
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
      
      #print "Traded amount: %s, traded price: %s" % (tradedAmount, ask['price'])
      
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
      
      #print "Traded amount: %s, traded price: %s" % (tradedAmount, bid['price'])
      
      bid['amount'] -= tradedAmount
      balance[pair[:3]] -= tradedAmount
      balance[pair[3:]] += tradedAmount * bid['price'] * k
      traded = True
      
      if bid['amount'] == Decimal('0'):
        self.depths[pair]['bid'] = self.depths[pair]['bid'][1:]
    
    remainingOrder['amount'] = remainder
    return (balance, remainingOrder, traded)
      
  
  def ModelTrade(self, balance, pair, type, price, amount):
    if not (pair in self.depths):
      return None
    
    price = self.tradeApi.FormatPrice(pair, price)
    amount = self.tradeApi.FormatAmount(pair, amount)
    
    print "ModelTrade: %s %s in %s for %s" % (type, amount, pair, price)
    
    balance2 = copy.deepcopy(balance)
    balance2, remainingOrder, traded = self.ModelL1Trade(balance, pair, type, price, amount)
    while traded:
      balance2, remainingOrder, traded = self.ModelL1Trade(balance, **remainingOrder)
      if remainingOrder['amount'] == Decimal('0'):
        break
    
    return (balance2, remainingOrder)

def CalculateArb(direction, price1, price2, price3, k):
  if price1 == None or price2 == None or price3 == None:
    return Decimal('0')
  if direction.lower() == 'forward':
    return k * k * k * price3 / (price1 * price2) - Decimal('1.0')
  elif direction.lower() == 'backward':
    return k * k * k * price1 * price2 / price3 - Decimal('1.0')
  else:
    return Decimal('0')
    
class ArbModel(object):
  def __init__(self, books, pair1, pair2, pair3, k):
    self.books = books
    self.pair1 = pair1
    self.pair2 = pair2
    self.pair3 = pair3
    self.k = k
  
  def priceLevelForDirection(self, direction, pairNo, depth):
    if direction.lower() == 'forward':
      if pairNo == 1:
        book = self.books[self.pair1]['ask']
      elif pairNo == 2:
        book = self.books[self.pair2]['ask']
      elif pairNo == 3:
        book = self.books[self.pair3]['bid']
      else:
        return (None, None)
    elif direction.lower() == 'backward':
      if pairNo == 1:
        book = self.books[self.pair1]['bid']
      elif pairNo == 2:
        book = self.books[self.pair2]['bid']
      elif pairNo == 3:
        book = self.books[self.pair3]['ask']
      else:
        return (None, None)
    else:
      return (None, None)
    
    if(len(book) <= depth or depth < 0):
      return (None, None)
    return (book[depth]['price'], book[depth]['amount'])
  
  def arbPercent(self, direction, depths = (0, 0, 0)):
    result = CalculateArb(direction, 
      self.priceLevelForDirection(direction, 1, depths[0])[0],
      self.priceLevelForDirection(direction, 2, depths[1])[0],
      self.priceLevelForDirection(direction, 3, depths[2])[0],
      self.k)
      
    return result
  
  def CalculateArbDepths(self):
    
    profitPercent = self.arbPercent('forward')
    profitPercentBackward = self.arbPercent('backward') 
    
    #print "profitPercent: %s, profitPercentBackward: %s" % (profitPercent, profitPercentBackward)
    
    if profitPercent > Decimal('0'):
      direction = 'forward'
    elif profitPercentBackward > Decimal('0'):
      direction = 'backward'
      profitPercent = profitPercentBackward
    else:
      return None
    
    depths = (0, 0, 0)
    
    #print "New depths: %s, profitPercent: %s" % (str(depths), profitPercent)
    
    addTuple = lambda t1, t2: tuple(e1 + e2 for e1, e2 in zip(t1, t2))
    
    condition = True
    #todo think about more clever way to find depths
    while condition:
      condition = False
      for x in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
        newDepths = addTuple(depths, x)
        profitPercent = self.arbPercent(direction, newDepths)
        #print "New depths: %s, profitPercent: %s" % (str(newDepths), profitPercent)
        if profitPercent > Decimal('0'):
          depths = newDepths
          condition = True
    
    return (direction, depths)

  def condenseOrders(self, pair, priceLevel, type):
    if type == 'bid':
      compare = lambda x, y: x >= y
      book = self.books[pair]['bid']
    elif type == 'ask':
      compare = lambda x, y: x <= y
      book = self.books[pair]['ask']
    else:
      return None
      
    price = Decimal('0.0')
    amount = Decimal('0.0')
    
    for level in book:
      if compare(level['price'], priceLevel):
        price = level['price']
        amount += level['amount']
      else:
        break
    return (price, amount)
    
  def CalculateArbLevels(self):
    r = self.CalculateArbDepths()
    if r == None:
      return None
      
    direction, depths = r
    if direction.lower() == 'forward':
      level1 = self.condenseOrders(self.pair1, 
        self.priceLevelForDirection(direction, 1, depths[0])[0],
        'ask')
      level2 = self.condenseOrders(self.pair2, 
        self.priceLevelForDirection(direction, 2, depths[1])[0],
        'ask')
      level3 = self.condenseOrders(self.pair3, 
        self.priceLevelForDirection(direction, 3, depths[2])[0],
        'bid')
    elif direction.lower() == 'backward':
      level1 = self.condenseOrders(self.pair1, 
        self.priceLevelForDirection(direction, 1, depths[0])[0],
        'bid')
      level2 = self.condenseOrders(self.pair2, 
        self.priceLevelForDirection(direction, 2, depths[1])[0],
        'bid')
      level3 = self.condenseOrders(self.pair3, 
        self.priceLevelForDirection(direction, 3, depths[2])[0],
        'ask')
    else:
      return None
    
    return (direction, level1, level2, level3, max(depths))
    
def CalculateArbOrders(books, pair1, pair2, pair3, k, balance, tradeApi):
  arbModel = ArbModel(books, pair1, pair2, pair3, k)
  r = arbModel.CalculateArbLevels()
  if r == None:
    return ([], 0)
  
  s1 = pair1[3:]
  s2 = pair1[:3]
  s3 = pair2[:3]
  
  direction, level1, level2, level3, maxDepth = r
  
  if direction == 'forward':
    a1 = level1[0]
    X = level1[1]
    a2 = level2[0]
    Y = level2[1]
    b3 = level3[0]
    Z = level3[1]
    
    usdToSpend = tradeApi.FormatPrice(pair1, 
      min(balance[s1], a1 / k * min(X, balance[s2]), a1 * a2 / (k*k) * min(Y, balance[s3]), a1 * a2 / (k*k*k) * Z))
      
    #print "balance: %s" % balance
    
    btcToBuy = tradeApi.FormatAmount(pair1, k * usdToSpend / a1)
    ltcToBuy = tradeApi.FormatAmount(pair2, k * btcToBuy / a2)
    
    if btcToBuy < tradeApi.GetMinAmount(pair1):
      print "%s to buy %s less than minimum %s" %(s2, btcToBuy, tradeApi.GetMinAmount(pair1))
      return ([], maxDepth)
      
    if ltcToBuy < min(tradeApi.GetMinAmount(pair2), tradeApi.GetMinAmount(pair3)):
      print "%s to buy %s less than minimum %s" %(s3, ltcToBuy, min(tradeApi.GetMinAmount(pair2), tradeApi.GetMinAmount(pair3)))
      return ([], maxDepth)
    
    return ([Order(pair1, 'buy', a1, btcToBuy), Order(pair2, 'buy', a2, ltcToBuy), Order(pair3, 'sell', b3, ltcToBuy)], maxDepth)
  elif direction == 'backward':
    b1 = level1[0]
    X = level1[1]
    b2 = level2[0]
    Y = level2[1]
    a3 = level3[0]
    Z = level3[1]
    
    usdToSpend = min(balance[s1], a3 / k * min(Z, balance[s3]), a3 / (k * k * b2) * min(Y * b2, balance[s2]), X * a3 / (k * k * k * b2))
    #print b1, b2, a3
    #print X, Y, Z
    #print balance[s1], a3 / k * min(Z, balance[s3]), a3 / (k * k * b2) * min(Y * b2, balance[s2]), X * a3 / (k * k * k * b2)
    print "usdToSpend: %s" % usdToSpend
    
    ltcToBuy = tradeApi.FormatAmount(pair3, k * usdToSpend / a3)
    btcToBuy = tradeApi.FormatAmount(pair1, k * ltcToBuy * b2)
    ltcToBuy = tradeApi.FormatAmount(pair3, btcToBuy / (k * b2))

    if btcToBuy < tradeApi.GetMinAmount(pair1):
      print "%s to buy %s less than minimum %s" %(s2, btcToBuy, tradeApi.GetMinAmount(pair1))
      return ([], maxDepth)
      
    if ltcToBuy < min(tradeApi.GetMinAmount(pair2), tradeApi.GetMinAmount(pair3)):
      print "%s to buy %s less than minimum %s" %(s3, ltcToBuy, min(tradeApi.GetMinAmount(pair2), tradeApi.GetMinAmount(pair3)))
      return ([], maxDepth)
    
    return ([Order(pair3, 'buy', a3, ltcToBuy), Order(pair2, 'sell', b2, ltcToBuy), Order(pair1, 'sell', b1, btcToBuy)], maxDepth)
  else:
    return ([], maxDepth)

    
    
    
  