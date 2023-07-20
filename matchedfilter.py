#!/usr/bin/python3

# This is the main-File.

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.uic import loadUi

import sys
import os
import templatebank_handler as handler  # selfmade; defines classes for matched filtering


### Get defaults
bankpath_default = 'C:/Users/Praktikum/Desktop/LIGO/template_bank/'
bankpath_default_2 = "C:/Users/Praktikum/Desktop/LIGO/template_bank"

### General settings
cwd = os.getcwd()
debugmode = True

mpi_path_host = cwd
mpi_path_container = '/input/mpi/'
connection = handler.connect()
### !!!!!!!!!!!!! could be removed in the end:
if debugmode: 
	connection.update_mpi(mpi_path_host, mpi_path_container)


class TemplateScreen(QMainWindow):

	def __init__(self, templatebank, labels=None):
		# general settings and initiation of ui
		super(TemplateScreen,self).__init__()
		loadUi(cwd+'/template_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Template Management)')
		self.templatebank = templatebank
		# connect Push Buttons
		self.pushButton_createTemplates.clicked.connect(self.create_templates)
		self.pushButton_loadDirectory.clicked.connect(self.load_directory)
		self.pushButton_loadFile.clicked.connect(self.load_file)
		self.pushButton_continue.clicked.connect(self.to_signal_screen)
		# set Status
		if labels:
			self.label_TempLine1.setText(labels[0])
			self.label_TempLine2.setText(labels[1])
			self.label_TempLine3.setText(labels[2])
			self.label_TempLine4.setText(labels[3])	

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
		files, _ = QFileDialog.getOpenFileNames(self,"Open Template-File(s)", bankpath_default_2,"All Files (*);;Python Files (*.py)", options=options)
		if files:
			return files

	def getDirectoryDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		options |= QFileDialog.ShowDirsOnly
		dirName = QFileDialog.getExistingDirectory(self, DialogName, defaultpath, options=options)+'/'
		if dirName:
			return dirName

	### methods connected with Push Buttons
	@pyqtSlot()
	def create_templates(self):
		print('Creating of new templates is not implemented yet.')
		return

	@pyqtSlot()
	def load_directory(self):
		path = self.getDirectoryDialog("Choose the directory to be loaded.", bankpath_default)
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

	@pyqtSlot()
	def to_signal_screen(self):
		labels = ( self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() )
		self.main = SignalScreen(self.templatebank, labels)
		self.main.show()
		self.close()

	### additional methods
	def make_label(self, string, maxlen, indent):
		'Cut a string from the start so it does not exceed maxlen, even with dots and indentation.'
		label = string
		if len(label) > (maxlen-indent):
			label = '...'+label[-(maxlen-indent-3):]
		label = ' '*indent+label
		return label

class SignalScreen(QMainWindow):

	def __init__(self, templatebank, labels):
		# general settings and initiation of ui
		super(SignalScreen,self).__init__()
		loadUi(cwd+'/signal_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc')
		self.templatebank = templatebank
		# connect Push Buttons
		self.pushButton_loadSignal.clicked.connect(self.load_signal)
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_go.clicked.connect(self.matched_filter)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		# set Status
		if labels:
			self.label_TempLine1.setText(labels[0])
			self.label_TempLine2.setText(labels[1])
			self.label_TempLine3.setText(labels[2])
			self.label_TempLine4.setText(labels[3])		

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
		files, _ = QFileDialog.getOpenFileNames(self,"Open Template-File(s)", bankpath_default_2,"All Files (*);;Python Files (*.py)", options=options)
		if files:
			return files

	def getDirectoryDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		options |= QFileDialog.ShowDirsOnly
		dirName = QFileDialog.getExistingDirectory(self, DialogName, defaultpath, options=options)+'/'
		if dirName:
			return dirName

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

	@pyqtSlot()
	def to_template_screen(self):
		labels = ( self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() )
		self.main = TemplateScreen(self.templatebank, labels)
		self.main.show()
		self.close()

	### additional methods
	def make_label(self, string, maxlen, indent):
		'Cut a string from the start so it does not exceed maxlen, even with dots and indentation.'
		label = string
		if len(label) > (maxlen-indent):
			label = '...'+label[-(maxlen-indent-3):]
		label = ' '*indent+label
		return label


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