#!/usr/bin/python3

# This is the main-File.

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QButtonGroup
from PyQt5.uic import loadUi

import sys
import os
from configparser import ConfigParser
import ast
import numpy as np
import templatebank_handler as handler  # selfmade; defines classes for matched filtering


### Get conifguration
config = ConfigParser()
config.read('config.ini')
OS = config.get('main', 'OS')
debugmode = config.get('main', 'debugmode')
bankpath = config.get('main', 'bankpath')


### General settings
cwd = os.getcwd()
mpi_path_host = cwd
mpi_path_container = '/input/mpi/'
connection = handler.connect()
### !!!!!!!!!!!!! could be removed in the end:
if debugmode: 
	connection.update_mpi(mpi_path_host, mpi_path_container)


class Screen(QMainWindow):   # Superclass where the different Screens following inherit common methods from.

	### initiation
	def __init__(self, templatebank, labels=None):
		super().__init__()
		# set status
		self.templatebank = templatebank
		self.labels = labels
	

	### label handling
	def show_labels(self):
		self.label_TempLine1.setText(self.labels[0])
		self.label_TempLine2.setText(self.labels[1])
		self.label_TempLine3.setText(self.labels[2])
		self.label_TempLine4.setText(self.labels[3])

	def make_label(self, string, maxlen, indent):
		'Cut a string from the start so it does not exceed maxlen, even with dots and indentation.'
		label = string
		if len(label) > (maxlen-indent):
			label = '...'+label[-(maxlen-indent-3):]
		label = ' '*indent+label
		return label


	### changing screens
	@pyqtSlot()
	def to_template_screen(self):
		self.main = TemplateScreen(self.templatebank, self.labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_signal_screen(self):
		labels = ( self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() )
		self.main = SignalScreen(self.templatebank, labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_create_screen(self):
		labels = ( self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() )
		self.main = CreateScreen(self.templatebank, labels)
		self.main.show()
		self.close()


	### methods for file-Dialogs
	# see: https://pythonspot.com/pyqt5-file-dialog/
	def openFileNameDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self, DialogName, defaultpath ,"All Files (*);;Python Files (*.py)", options=options)
		if fileName:
			return fileName

	def openFileNamesDialog(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open Template-File(s)", bankpath,"All Files (*);;Python Files (*.py)", options=options)
		if files:
			return files

	def getDirectoryDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		options |= QFileDialog.ShowDirsOnly
		dirName = QFileDialog.getExistingDirectory(self, DialogName, defaultpath, options=options)+'/'
		if dirName:
			return dirName



class TemplateScreen(Screen):

	def __init__(self, templatebank, labels=None):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/template_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Template Management)')
		self.templatebank = templatebank
		if labels: self.show_labels()
		# connect Push Buttons
		self.pushButton_createTemplates.clicked.connect(self.to_create_screen)
		self.pushButton_loadDirectory.clicked.connect(self.load_directory)
		self.pushButton_loadFile.clicked.connect(self.load_file)
		self.pushButton_continue.clicked.connect(self.to_signal_screen)

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_directory(self):
		path = self.getDirectoryDialog("Choose the directory to be loaded.", bankpath)
		self.templatebank.add_directory(path)
		label = self.make_label(path, 48, 8)
		if not self.label_TempLine3.text()=='None':
			self.label_TempLine4.setText('and more')
		self.label_TempLine3.setText(self.label_TempLine2.text())
		self.label_TempLine2.setText(self.label_TempLine1.text())
		self.label_TempLine1.setText(label)
		self.show()
		return

	@pyqtSlot()
	def load_file(self):
		fullname = self.openFileNamesDialog()[0]
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.templatebank.add_template(path, filename)
		label = self.make_label(fullname, 48, 8)
		if not self.label_TempLine3.text()=='None':
			self.label_TempLine4.setText('and more')
		self.label_TempLine3.setText(self.label_TempLine2.text())
		self.label_TempLine2.setText(self.label_TempLine1.text())
		self.label_TempLine1.setText(label)
		self.show()
		return


class CreateScreen(Screen):

	def __init__(self, templatebank, labels=None):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/create_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Template Creation)')
		self.templatebank = templatebank
		self.labels = labels
		self.flag_Mr = True
		self.flag_All = True
		self.path = bankpath
		self.label_path.setText(self.path)
		# connect pushButtons
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_create.clicked.connect(self.create_templates)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		# set up radioButtons
		self.ButtonGroup_Parameter = QButtonGroup()
		self.ButtonGroup_Parameter.addButton(self.radioButton_Mr, id=1)
		self.ButtonGroup_Parameter.addButton(self.radioButton_m1m2, id=2)
		self.radioButton_Mr.setChecked(True)
		self.ButtonGroup_Parameter.buttonClicked.connect(self.change_Parameter)
		self.ButtonGroup_All = QButtonGroup()
		self.ButtonGroup_All.addButton(self.radioButton_AllOn, id=3)
		self.ButtonGroup_All.addButton(self.radioButton_AllOff, id=4)
		self.radioButton_AllOn.setChecked(True)
		self.ButtonGroup_All.buttonClicked.connect(self.change_All)
		# set up checkBoxes
		self.checkBox_Para1Code.setChecked(False)
		self.checkBox_Para2Code.setChecked(False)
		self.checkBox_freq.setChecked(True)
		self.checkBox_time.setChecked(False)

	@pyqtSlot()
	def change_output(self):
		self.path = self.getDirectoryDialog('Choose the new output directory.', self.path)
		self.label_path.setText(self.make_label(self.path,120,0))
		self.show()

	@pyqtSlot()
	def change_Parameter(self):
		'Change the Layout and flag_Mr, if one of the Parameter radioButtons is clicked.'
		if self.ButtonGroup_Parameter.checkedId() == 1:
			self.flag_Mr = True
			self.label_Parameter1.setText('total mass (M)')
			self.label_Parameter2.setText('mass ratio (r)')
			self.label_FilenameExt.setText("+'Mr-[index]_[M]-[r]'")
			self.show()
			if debugmode: print('Mr')
		else:
			self.flag_Mr = False
			self.label_Parameter1.setText('mass 1 (m1)')
			self.label_Parameter2.setText('mass 2 (m2)')
			self.label_FilenameExt.setText("+'mm-[index]_[m1]-[m2]'")
			self.show()
			if debugmode: print('m1m2')

	@pyqtSlot()
	def change_All(self):
		'Change the Layout and flag_All, if one of the All radioButtons is clicked.'
		if self.ButtonGroup_All.checkedId() == 3:
			self.flag_All = True
			if debugmode: print('AllOn')
		else:
			self.flag_All = False
			if debugmode: print('AllOf')

	def get_array(self):
		'Convert input from the lineEdit fields into the appropriate 2d numpy array.'

		# get first sub-array
		if self.checkBox_Para1Code.isChecked():
			array1 = ast.literal_eval(self.lineEdit_Para1Code.text())
		else:
			start1 = float(ast.literal_eval(self.lineEdit_Para1Start.text()))
			stop1 = float(ast.literal_eval(self.lineEdit_Para1Stop.text()))
			num1 = int(ast.literal_eval(self.lineEdit_Para1Number.text()))
			array1 = np.linspace(start1,stop1, num=num1, endpoint=True)
		
		# get second sub-array
		if self.checkBox_Para2Code.isChecked():
			array2 = ast.literal_eval(self.lineEdit_Para2Code.text())
		else:			
			start2 = float(ast.literal_eval(self.lineEdit_Para2Start.text()))
			stop2 = float(ast.literal_eval(self.lineEdit_Para2Stop.text()))
			num2 = int(ast.literal_eval(self.lineEdit_Para2Number.text()))
			array2 = np.linspace(start2, stop2, num=num2, endpoint=True)

		# merge according to flag_All
		pre_array = np.asarray((array1,array2))
		if self.flag_All:
			array = np.zeros( (2, len(pre_array[0])*len(pre_array[1])) )
			counter = 0
			for elem1 in pre_array[0]:
				for elem2 in pre_array[1]:
					array[0][counter] = elem1
					array[1][counter] = elem2
					counter += 1
		else:
			length = np.minimum( len(pre_array[0]), len(pre_array[1]) )
			array = np.asarray( (array1[:length], array2[:length]) )

		return array


	@pyqtSlot()
	def create_templates(self):
		'Create templates from the user-input.'
		################   !!!!!!!!!!!!!!!!!!     I should call an Error here. (following line)
		if not os.path.isdir(self.path): print('Output path does not exist.')
		array = self.get_array()
		basename = self.lineEdit_FilenameBase.text()
		if debugmode: print('basename = ',basename)
		freq_domain = self.checkBox_freq.isChecked()
		time_domain = self.checkBox_time.isChecked()
		self.templatebank.create_templates(array, self.path, basename, self.flag_Mr, freq_domain, time_domain)

	

class SignalScreen(Screen):

	def __init__(self, templatebank, labels):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/signal_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Matched Filtering)')
		self.templatebank = templatebank
		# connect Push Buttons
		self.pushButton_loadSignal.clicked.connect(self.load_signal)
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_go.clicked.connect(self.matched_filter)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		# set Status
		if labels: self.show_labels()

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_signal(self):
		fullname = self.openFileNameDialog("Open Signal-File", "C:/Users/Praktikum/Desktop/LIGO")
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.data = handler.Data(path, filename)
		self.label_Signal.setText( self.make_label(fullname, 35, 2) )
		self.label_Output.setText( self.make_label(self.data.savepath,35,2) )
		self.show()
		return

	@pyqtSlot()
	def change_output(self):
		newpath = self.getDirectoryDialog('Choose the new output directory.', self.data.datapath)
		self.data.set_savepath(newpath)
		self.label_Output.setText( self.make_label(self.data.savepath,35,2) )
		self.show()
		return

	@pyqtSlot()
	def matched_filter(self):
		self.data.matched_filter_templatebank(self.templatebank, connection)
		return


# open Window
# -----------

with open('matchedfilter.qss','r') as qss:
	style = qss.read()

app = QApplication(sys.argv)
app.setStyleSheet(style)
templatebank = handler.TemplateBank()
win = TemplateScreen(templatebank)
win.show()
sys.exit(app.exec_())