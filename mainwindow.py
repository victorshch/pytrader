import sys
import decimal
from decimal import Decimal
import PyQt4
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSlot
import traderthread
from traderthread import Tops, ArbData
import ui_mainwindow
from ui_mainwindow import Ui_MainWindow

class MainWindow(QtGui.QMainWindow):
  def __init__(self, exchangeName):
    QtGui.QMainWindow.__init__(self)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.setWindowTitle('PyArbitrageTrader - ' + exchangeName)
    
    self.maxProfit = Decimal('-1')
    
    self.model = QtGui.QStandardItemModel()
    self.model.setHorizontalHeaderLabels(["Time",
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
    self.ui.tableView_history.setModel(self.model)

  
  @pyqtSlot(int)
  def receiveLag(self, lag):
    self.ui.spinBox_lag.setValue(lag)
  
  @pyqtSlot(Tops, ArbData, ArbData)
  def receiveUpdate(self, tops, a1, a2):
    self.ui.doubleSpinBox_sec1_ask.setValue(float(tops.ask1))
    self.ui.doubleSpinBox_sec1_bid.setValue(float(tops.bid1))
    self.ui.doubleSpinBox_sec2_ask.setValue(float(tops.ask2))
    self.ui.doubleSpinBox_sec2_bid.setValue(float(tops.bid2))
    self.ui.doubleSpinBox_sec3_ask.setValue(float(tops.ask3))
    self.ui.doubleSpinBox_sec3_bid.setValue(float(tops.bid3))
    
    self.ui.doubleSpinBox_sec1_askAmount.setValue(float(tops.ask1_amount))
    self.ui.doubleSpinBox_sec1_bidAmount.setValue(float(tops.bid1_amount))
    self.ui.doubleSpinBox_sec2_askAmount.setValue(float(tops.ask2_amount))
    self.ui.doubleSpinBox_sec2_bidAmount.setValue(float(tops.bid2_amount))
    self.ui.doubleSpinBox_sec3_askAmount.setValue(float(tops.ask3_amount))
    self.ui.doubleSpinBox_sec3_bidAmount.setValue(float(tops.bid3_amount))
    
    self.maxProfit = max(self.maxProfit, a1.profit, a2.profit)
    
    result_text = "profit1 = %s\nprofit2 = %s\nmaxProfit = %s" % (a1.profit, a2.profit, self.maxProfit)
    self.ui.label_result.setText(result_text)

    lastItem = None
    
    if a1.profit > 0 or a2.profit > 0:
      a = a1 if a1.profit > 0 else a2
      
      print("Got arbitrage opportunity with profit %s" % a.profit)
      
      lastItem = QtGui.QStandardItem()
      lastItem.setText(str(a.usdProfit))
      lastItem.setToolTip(str(a.usdInvestment))
      
      self.model.appendRow([QtGui.QStandardItem(str(QtCore.QDateTime.currentDateTime().toString())),
      QtGui.QStandardItem(a.tradeDirection),
      QtGui.QStandardItem(str(tops.ask1)),
      QtGui.QStandardItem(str(tops.ask1_amount)),
      QtGui.QStandardItem(str(tops.bid1)),
      QtGui.QStandardItem(str(tops.bid1_amount)),
      QtGui.QStandardItem(str(tops.ask2)),
      QtGui.QStandardItem(str(tops.ask2_amount)),
      QtGui.QStandardItem(str(tops.bid2)),
      QtGui.QStandardItem(str(tops.bid2_amount)),
      QtGui.QStandardItem(str(tops.ask3)),
      QtGui.QStandardItem(str(tops.ask3_amount)),
      QtGui.QStandardItem(str(tops.bid3)),
      QtGui.QStandardItem(str(tops.bid3_amount)),
      QtGui.QStandardItem(str(a.profit * Decimal('100')) + "%"),
      lastItem])
      
      self.model.reset()
    
    
  #todo