import sys 
import os
import time
from PyQt5.QtGui import QRegExpValidator, QDoubleValidator
from PyQt5.QtWidgets import (QApplication, QPushButton, QWidget, QComboBox, 
QHBoxLayout, QVBoxLayout, QFormLayout, QCheckBox, QGridLayout, QDialog, 
QLabel, QLineEdit, QDialogButtonBox, QFileDialog, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QRegExp, QCoreApplication
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from random import randint
import serial
import serial.tools.list_ports
import numpy as np
import psutil
import csv
import qdarkstyle

#Drone: 2 inputs, 4 outputs
#Pro Con: 1 input, 2 outputs
#Fixes Scaling for high resolution monitors
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

class SerialComm:
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout    

    def serialOpen(self):
        self.ser = serial.Serial(port = self.port,
                                 baudrate = self.baudrate,
                                 timeout = self.timeout)
        return(self.ser)
    
    """
    handshake() method written for now. Will not have functionality yet.
    """
    def handshake(self):
        self.ser.flushInput()
        self.ser.write(b"A")
        print("Handshake request sent")
        response = self.ser.readline().decode().replace('\r\n','')
        
        if(response == "Contact established"):
            print("Handshake success")
        
        else:
            print("Handshake failed")
            self.handshake()

    def readValues(self):
        arduinoData = self.ser.readline().decode().replace('\r\n','').split(",")
        return arduinoData        
    
    def writeValues(self):
        pass


class Dialog1(QDialog):
    def __init__(self, *args, **kwargs):
        super(Dialog1, self).__init__(*args, **kwargs)
        
        self.title = "Settings"
        self.setWindowTitle(self.title)        
        self.setModal(True)
        self.width = 200
        self.height = 200
        self.setFixedSize(self.width, self.height)
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        mainLayout = QHBoxLayout() 
        leftFormLayout = QFormLayout()
        mainLayout.addLayout(leftFormLayout,100)

        self.port_label = QLabel("Ports:",self)
        #self.port_label.setStyleSheet("font-size:12pt;")
        
        self.port = QComboBox(self)
        self.port.setFixedWidth(100)
        #self.port.setStyleSheet("font-size:12pt;")
        self.list_port()

        self.baudrate_label = QLabel("Baud Rate:",self)
        #self.baudrate_label.setStyleSheet("font-size:12pt;")

        self.baudrate = QComboBox(self)
        self.baudrate.setFixedWidth(100)
        #self.baudrate.addItems(["4800","9600","14400"])
        self.baudrate.addItems(["9600","14400"])
        #self.baudrate.setStyleSheet("font-size:12pt;")
        
        self.timeout_label = QLabel("Timeout:",self)
        #self.timeout_label.setStyleSheet("font-size:12pt;")

        self.timeout = QLineEdit(self)
        self.timeout.setFixedWidth(100)
        #self.timeout.setStyleSheet("font-size:12pt;")
        self.timeout.setText("2")

        #For now, it will be 0-255 (FIX THIS IN FUTURE; Timeout in increments of 1s to 255s is weird)
        #regex = QRegExp("^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$")
        #regex_validator_timeout = QRegExpValidator(regex,self)

        #self.timeout.setValidator(regex_validator_timeout)
        self.timeout.setValidator(QDoubleValidator())
        
        self.samplenum_label = QLabel("Sample #:",self)
        #self.samplenum_label.setStyleSheet("font-size:12pt;")

        self.samplenum = QLineEdit(self)
        self.samplenum.setFixedWidth(100)
        #self.samplenum.setStyleSheet("font-size:12pt;")
        self.samplenum.setText("100")

        #For now, it will be 0-255 (FIX THIS IN FUTURE; 0 samples makes no sense)
        regex = QRegExp("^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$")
        regex_validator_samplenum = QRegExpValidator(regex,self)

        self.samplenum.setValidator(regex_validator_samplenum)

        #Ok and cancel button
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
       
        leftFormLayout.addRow(self.port_label,self.port)
        leftFormLayout.addRow(self.baudrate_label,self.baudrate)
        leftFormLayout.addRow(self.timeout_label,self.timeout)
        leftFormLayout.addRow(self.samplenum_label,self.samplenum)
        leftFormLayout.addRow(buttonBox)

        self.setLayout(mainLayout)


    def list_port(self): #currently only works with genuine Arduinos due to parsing method
        arduino_ports = [
            p.device
            for p in serial.tools.list_ports.comports()
            if 'Arduino' in p.description  
        ]
        if not arduino_ports:
            raise IOError("No Arduino found. Replug in USB cable and try again.")
        self.port.addItems(arduino_ports)


    def getDialogValues(self):
        if self.exec_() == QDialog.Accepted:
            self.com_value = str(self.port.currentText())
            self.baudrate_value = str(self.baudrate.currentText())
            self.timeout_value = float(self.timeout.text())
            self.samplenum_value = int(self.samplenum.text())
            return([self.com_value, self.baudrate_value, self.timeout_value, self.samplenum_value])

        else:
            print("Settings Menu Closed")
    

class Window(QWidget):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        
        #Application Title
        self.title = "Drone Control"
        self.setWindowTitle(self.title)

        #Application Size
        self.left = 100
        self.top = 100
        self.width = 1000
        self.height = 700
        self.setGeometry(self.left, self.top, self.width, self.height)
        #self.setFixedSize(self.width,self.height)


        self.initUI()

    def initUI(self):
        #self.setStyleSheet("font-size:12pt")

        """
        Change this to your current relative/absolute path. Will be fixed in final version.
        """
        #self.setStyleSheet(open(r".\Arduino\qdarkstyle\style.qss", "r").read()) #relaitve
        #self.setStyleSheet(open(r"C:\Users\qwert\Desktop\Python VSCode\Arduino\qdarkstyle\style.qss", "r").read()) #absolute
        self.setStyleSheet(qdarkstyle.load_stylesheet())
        mainLayout = QHBoxLayout()
        """        
        #leftMajor = QVBoxLayout()
        leftMajor = QGridLayout()
        leftMajor.setSpacing(20)
        
        leftFormLayout = QFormLayout() #only had this
        gridtest = QGridLayout()
        gridtest.setSpacing(10)

        leftMajor.addLayout(leftFormLayout)
        leftMajor.addLayout(gridtest)
        
        rightLayout = QVBoxLayout()
        mainLayout.addLayout(leftMajor,20)
        #mainLayout.addLayout(leftFormLayout,20)
        mainLayout.addLayout(rightLayout,150)
        """
        mainLayout = QHBoxLayout()  
        leftFormLayout = QFormLayout()
        rightLayout = QVBoxLayout()
        mainLayout.addLayout(leftFormLayout,20)
        mainLayout.addLayout(rightLayout,150)
        

        self.startbutton = QPushButton("Start",self)
        self.startbutton.setCheckable(False)  
        self.startbutton.clicked.connect(self.startbutton_pushed)
        self.startbutton.resize(100,20)
        self.startbutton.setFixedWidth(100)

        self.stopbutton = QPushButton("Stop",self)
        self.stopbutton.setCheckable(False)  
        self.stopbutton.clicked.connect(self.stopbutton_pushed)
        self.stopbutton.resize(100,20)
        self.stopbutton.setFixedWidth(100)

        self.clearbutton = QPushButton("Clear",self)
        self.clearbutton.setCheckable(False)
        self.clearbutton.clicked.connect(self.clearbutton_pushed)
        self.clearbutton.resize(100,20)
        self.clearbutton.setFixedWidth(100)

        self.savebutton = QPushButton("Save",self)
        self.savebutton.setCheckable(False)
        self.savebutton.clicked.connect(self.savebutton_pushed)
        self.savebutton.resize(100,20)        
        self.savebutton.setFixedWidth(100)

        self.checkBoxShowAll = QCheckBox("Show All Plots", self)
        self.checkBoxShowAll.setChecked(True)
        self.checkBoxShowAll.toggled.connect(self.visibilityAll)

        self.checkBoxHideAll = QCheckBox("Hide All Plots", self)
        self.checkBoxHideAll.setChecked(False)
        self.checkBoxHideAll.toggled.connect(self.hideAll)

        self.checkBoxPlot1 = QCheckBox("Plot 1", self)
        self.checkBoxPlot1.toggled.connect(self.visibility1)
        
        self.checkBoxPlot2 = QCheckBox("Plot 2", self)
        self.checkBoxPlot2.toggled.connect(self.visibility2)

        self.AmplitudeLabel = QLabel("Amplitude",self)
        self.AmplitudeInput = QLineEdit("",self)
        self.AmplitudeInput.setValidator(QDoubleValidator())
        #self.AmplitudeInput.conn

        self.FrequencyLabel = QLabel("Frequency (Hz)",self)
        self.FrequencyInput = QLineEdit("",self)
        self.FrequencyInput.setValidator(QDoubleValidator())

        self.PCheckBox = QCheckBox("P",self)
        self.PCheckBox.setChecked(True)
        self.PCheckBox.toggled.connect(self.PCheckBoxLogic)

        self.PInput = QLineEdit("",self)
        self.PInput.setValidator(QDoubleValidator())

        self.ICheckBox = QCheckBox("I",self)
        self.ICheckBox.setChecked(True)
        self.ICheckBox.toggled.connect(self.ICheckBoxLogic)

        self.IInput = QLineEdit("",self)    
        self.IInput.setValidator(QDoubleValidator())

        self.DCheckBox = QCheckBox("D",self)
        self.DCheckBox.setChecked(True)
        self.DCheckBox.toggled.connect(self.DCheckBoxLogic)
        
        self.DInput = QLineEdit("",self)
        self.DInput.setValidator(QDoubleValidator())

        self.checkBoxShowAll.stateChanged.connect(self.checkbox_logic) 
        self.checkBoxHideAll.stateChanged.connect(self.checkbox_logic) 
        self.checkBoxPlot1.stateChanged.connect(self.checkbox_logic) 
        self.checkBoxPlot2.stateChanged.connect(self.checkbox_logic) 

        self.settings = QPushButton("Settings",self)
        self.settings.clicked.connect(self.settingsMenu)
        #self.settings.setFixedWidth(205)
            
        self.inputForms = QComboBox()
        self.inputForms.addItems(["Sine","Step"])
        self.inputForms.activated.connect(self.getInput)

        #Creates Plotting Widget        
        self.graphWidgetOutput = pg.PlotWidget()
        self.graphWidgetInput = pg.PlotWidget()
        #state = self.graphWidget.getState()

        #Adds grid lines
        self.graphWidgetOutput.showGrid(x = True, y = True, alpha=None)
        self.graphWidgetInput.showGrid(x = True, y = True, alpha=None)

        #self.graphWidget.setXRange(0, 100, padding=0) #Doesn't move with the plot. Can drag around
        #self.graphWidget.setLimits(xMin=0, xMax=100)#, yMin=c, yMax=d) #Doesn't move with the plot. Cannot drag around

        #self.graphWidget.setYRange(0, 4, padding=0)
        self.graphWidgetOutput.setYRange(-11, 11, padding=0)
        self.graphWidgetOutput.enableAutoRange()
        self.graphWidgetInput.setYRange(-11, 11, padding=0)
        self.graphWidgetInput.enableAutoRange()
        
        #Changes background color of graph
        self.graphWidgetOutput.setBackground((0,0,0))
        self.graphWidgetInput.setBackground((0,0,0))

        #Adds title to graphs
        self.graphWidgetOutput.setTitle("Output", color="w", size="14pt")
        self.graphWidgetInput.setTitle("Input", color="w", size="14pt")

        
        #Positioning the buttons and checkboxes
        #leftFormLayout.setContentsMargins(70,100,10,10)
        leftFormLayout.addRow(self.startbutton,self.stopbutton)
        leftFormLayout.addRow(self.clearbutton,self.savebutton)
        leftFormLayout.addRow(self.settings)
        leftFormLayout.addRow(self.checkBoxShowAll)
        leftFormLayout.addRow(self.checkBoxHideAll)
        leftFormLayout.addRow(self.checkBoxPlot1)
        leftFormLayout.addRow(self.checkBoxPlot2)
        leftFormLayout.addRow(self.inputForms)
        leftFormLayout.addRow(self.AmplitudeLabel,self.AmplitudeInput)
        leftFormLayout.addRow(self.FrequencyLabel,self.FrequencyInput)
        leftFormLayout.addRow(self.PCheckBox,self.PInput)
        leftFormLayout.addRow(self.ICheckBox,self.IInput)
        leftFormLayout.addRow(self.DCheckBox,self.DInput)

        rightLayout.addWidget(self.graphWidgetOutput)
        rightLayout.addWidget(self.graphWidgetInput)
        """
        gridtest.addWidget(self.PCheckBox,0,0)
        gridtest.addWidget(self.PInput,0,1)    
        gridtest.addWidget(self.ICheckBox,1,0)
        gridtest.addWidget(self.IInput,1,1)  
        gridtest.addWidget(self.DCheckBox,2,0)
        gridtest.addWidget(self.DInput,2,1)  
        """
        self.setLayout(mainLayout)
        
        #Plot time update settings
        self.timer = QTimer()
        self.timer.setInterval(50) #Changes the plot speed
        self.initialState()
        time.sleep(2)
        try:
            self.timer.timeout.connect(self.updatePlot1)
        except:
            raise Exception("Missing 1")
        try:
            self.timer.timeout.connect(self.updatePlot2)
        except:
            raise Exception("Missing 2")
        #self.show()

    #Checkbox logic
    def checkbox_logic(self, state): 
  
        # checking if state is checked 
        if state == Qt.Checked: 
  
            # if first check box is selected 
            if self.sender() == self.checkBoxShowAll: 
                self.checkBoxHideAll.setChecked(False) 
                self.checkBoxPlot1.setChecked(False)
                self.checkBoxPlot2.setChecked(False)
                #self.checkBoxShow.stateChanged.disconnect(self.uncheck) 
  
            elif self.sender() == self.checkBoxHideAll:
                #self.checkBoxShow.stateChanged.connect(self.uncheck)      
                self.checkBoxShowAll.setChecked(False) 
                self.checkBoxPlot1.setChecked(False) 
                self.checkBoxPlot2.setChecked(False)   
            
            elif self.sender() == self.checkBoxPlot1: 
                self.checkBoxShowAll.setChecked(False) 
                self.checkBoxHideAll.setChecked(False)
                self.checkBoxPlot2.setChecked(False)

            elif self.sender() == self.checkBoxPlot2:
                self.checkBoxShowAll.setChecked(False) 
                self.checkBoxHideAll.setChecked(False)
                self.checkBoxPlot1.setChecked(False)

    #Button/Checkbox Connections
    #Start Button
    def startbutton_pushed(self):
        self.initialState()
        self.ser = serial.Serial(port = self.serial_values[0], 
                                 baudrate = self.serial_values[1],
                                 timeout = self.serial_values[2])
        self.timer.start()
        self.plotting1()
        self.plotting2()
        self.startbutton.clicked.disconnect(self.startbutton_pushed)

    #Stop Button
    def stopbutton_pushed(self):
        self.timer.stop()
        self.ser.close()
        try:
            print(self.x)
            print(len(self.x))
        except:
            print("Missing x")
        try:
            print(self.y1)
            print(len(self.y1))
        except:
            print("Missing y1")
        try:
            print(self.y2)
            print(len(self.y2))
        except:
            print("Missing y2")
        #self.initialState()

    #Clear Button
    def clearbutton_pushed(self):
        self.graphWidgetOutput.clear()
        self.graphWidgetInput.clear()
        self.graphWidgetOutput.enableAutoRange(axis=None, enable=True, x=None, y=None)
        self.startbutton.clicked.connect(self.startbutton_pushed)
    
    def savebutton_pushed(self):
        self.createCSV()
        path = QFileDialog.getSaveFileName(self, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if path[0] != '':
            with open(path[0], 'w', newline = '') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(self.header)
                csvwriter.writerows(self.data_set)
    
    def createCSV(self):
        # INCOMPLETE DATA. Saves only 25 points in all arrays.
        self.header = ['x1', 'y1', 'x2', 'y2']
        self.data_set = zip(self.x1,self.y1,self.x2,self.y2)

    def initialState(self):
        #Windowed data. What is being shown on the graphs
        self.x1 = list(range(25)) #waits for x, y1, and y2 to be 0-24 samples
        self.x2 = list(range(25))
        self.y1 = list()
        self.y2 = list()

        #Complete data. What will be written to the csv file
        self.x1_full = list()
        self.x2_full = list()
        self.y1_full = list()
        self.y2_full = list()

    def readValues(self):
        arduinoData = self.ser.readline().decode().replace('\r\n','').split(",")
        return arduinoData

    def plotting1(self):
        a = self.readValues()
        while len(self.y1) != 25:
            self.y1.append(float(a[0]))
        pen1 = pg.mkPen(color = (255, 0, 0), width=1)
        self.data1 = self.graphWidgetOutput.plot(self.x1, self.y1, pen = pen1)

    def plotting2(self):
        b = self.readValues()
        while len(self.y2) != 25:
            self.y2.append(float(b[0]))
        pen2 = pg.mkPen(color = (0, 255, 0), width=1)
        self.data2 = self.graphWidgetOutput.plot(self.x2, self.y2, pen = pen2)

    def updatePlot1(self):
        a = self.readValues()
        self.x1 = self.x1[1:]  
        self.x1.append(self.x1[-1] + 1)  
        self.y1 = self.y1[1:]  
        self.y1.append(float(a[0]))
        self.data1.setData(self.x1, self.y1)  
        #print(psutil.virtual_memory())

    def updatePlot2(self):
        b = self.readValues()
        self.x2 = self.x2[1:]  
        self.x2.append(self.x2[-1] + 1)  
        self.y2 = self.y2[1:]   
        self.y2.append(float(b[1]))
        self.data2.setData(self.x2, self.y2) 
        #print(psutil.virtual_memory())

    def visibilityAll(self):
        showall = self.sender()
        if showall.isChecked() == True:
            self.data1.setVisible(True)
            self.data2.setVisible(True) 

    def hideAll(self):
        disappearall = self.sender()
        if disappearall.isChecked() == True:
            self.data1.setVisible(False)
            self.data2.setVisible(False)

    def visibility1(self):
        test1 = self.sender()
        if test1.isChecked() == True:
            self.data1.setVisible(True)
            self.data2.setVisible(False)
    
    def visibility2(self):
        test2 = self.sender()
        if test2.isChecked() == True:
            self.data2.setVisible(True)
            self.data1.setVisible(False)

    def settingsMenu(self):
        self.settingsPopUp = Dialog1()
        self.settingsPopUp.show()
        #self.settingsPopUp.exec()
        self.serial_values = self.settingsPopUp.getDialogValues()

    def PCheckBoxLogic(self):
        test1 = self.sender()
        if test1.isChecked() == True:
            self.PInput.setEnabled(True)
        elif test1.isChecked() == False:
            self.PInput.setEnabled(False)

    def ICheckBoxLogic(self):
        test1 = self.sender()
        if test1.isChecked() == True:
            self.IInput.setEnabled(True)
        elif test1.isChecked() == False:
            self.IInput.setEnabled(False)

    def DCheckBoxLogic(self):
        test1 = self.sender()
        if test1.isChecked() == True:
            self.DInput.setEnabled(True)
        elif test1.isChecked() == False:
            self.DInput.setEnabled(False)

    def PIDInput(self):
        if self.PInput.text() == "" or self.PCheckBox.checkState() == False:
            self.Pvalue = 0
        else:
            self.Pvalue = self.PInput.text()

        if self.IInput.text() == "" or self.ICheckBox.checkState() == False:
            self.Ivalue = 0
        else:
            self.Ivalue = self.IInput.text()

        if self.DInput.text() == "" or self.DCheckBox.checkState() == False:
            self.Dvalue = 0
        else:
            self.Dvalue = self.DInput.text()
        return([self.Pvalue, self.Ivalue, self.Dvalue])

    def WriteValues(self):
        pass

    #Function that connects output pyqtgraph widget, and the combobox
    def getInput(self):
        self.inputType = str(self.inputForms.currentText())
        pen_input = pg.mkPen(color = (255, 0, 0), width=1)

        if self.inputType == "Sine":
            print("Sine")
            self.graphWidgetInput.clear()
            self.x_input = np.arange(0,10,0.1)
            self.y_input = np.sin(self.x_input)
            self.data_input = self.graphWidgetInput.plot(self.x_input, self.y_input, pen = pen_input)
            self.data_input.setData(self.x_input, self.y_input)  
            self.graphWidgetInput.setYRange(-2, 2, padding=0)

        elif self.inputType == "Step":
            print("Step")
            self.graphWidgetInput.clear()
            self.x_input = np.arange(0,10,0.1)
            self.y_input = np.heaviside(self.x_input,1)
            self.data_input = self.graphWidgetInput.plot(self.x_input, self.y_input, pen = pen_input)
            self.data_input.setData(self.x_input, self.y_input)
            self.graphWidgetInput.setYRange(-2, 2, padding=0)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main = Window()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()