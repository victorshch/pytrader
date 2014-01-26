import sys
import time
from spreadsheethandler import SpreadsheetHandler
from tradeapi import CreateTradeApi

tradeApi = None
exchangeName = ''

if(len(sys.argv) > 1):
  exchangeName = sys.argv[1]
else:
  exchangeName = 'btce'

tradeApi = CreateTradeApi(exchangeName, ['balance-watcher-keyfile.txt'])

sKeyFile = open('balance-table.txt')
sKey = next(sKeyFile)

sHandler = SpreadsheetHandler('spreadsheet-key.txt', sKey, 'Balance watcher')

balance = tradeApi.GetBalance(['btc', 'ltc', 'usd', 'ppc', 'nmc', 'nvc'])

balance['time'] = time.strftime('%m/%d/%Y %H:%M:%S')

sHandler.AddRow(tradeApi.Name(), balance)
print balance





