#!/usr/bin/python3

# This is the main-File.

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QButtonGroup
from PyQt5.uic import loadUi
import threading

import sys
import os
from configparser import ConfigParser
import ast
import numpy as np
import templatebank_handler as handler  # selfmade; defines classes for matched filtering

# for the plot
import time
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qtagg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


### worker objects for threading

class CreateTemplatesWorker(QObject):
	finished = pyqtSignal()
	progress = pyqtSignal(int)

	def __init__(self, templatebank, array, path, basename, flag_Mr, freq_domain, time_domain):
		super().__init__()
		self.templatebank = templatebank
		self.array = array
		self.path = path
		self.basename = basename
		self.flag_Mr = flag_Mr
		self.freq_domain = freq_domain
		self.time_domain = time_domain

	def create_templates(self):
		'Create templates from the user-input.'
		################   !!!!!!!!!!!!!!!!!!     I should call an Error here. (following line)
		if not os.path.isdir(self.path): print('Output path does not exist.')
		self.progress.emit(0)
		templatebank.create_templates(self.array, self.path, self.basename, self.flag_Mr, self.freq_domain, self.time_domain)
		self.progress.emit(1)
		# add the new templates to the templatebank
		self.templatebank.add_directory(self.path)
		self.progress.emit(2)
		self.finished.emit()

		### lets not implement this not, but later                 ######################################
		# label = self.make_label(self.path, 48, 8)
		# if not self.labels[2]=='None':
		# 	self.labels[3] = 'and more'
		# self.labels[2] = self.labels[1]
		# self.labels[1] = self.labels[0]
		# self.labels[0] = label
		# self.show()


class MatchedFilteringWorker(QObject):
	finished = pyqtSignal()
	progress = pyqtSignal(int)

	def __init__(self, data, templatebank, connection):
		super().__init__()
		self.data = data
		self.templatebank = templatebank
		self.connection = connection

	def matched_filter(self):
		self.data.matched_filter_templatebank(self.templatebank, connection)
		self.finished.emit()

	# Look at the Worker above for how feedback could be sent back.


### Screen objects

class Screen(QMainWindow):   # Superclass where the different Screens following inherit common methods from.

	### initiation
	def __init__(self, config, templatebank, data=None, labels=None):
		super().__init__()
		# set status
		self.config = config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels
	

	### label handling
	def make_label(self, string, maxlen, indent):
		'Cut a string from the start so it does not exceed maxlen, even with dots and indentation.'
		label = string
		if len(label) > (maxlen-indent):
			label = '...'+label[-(maxlen-indent-3):]
		label = ' '*indent+label
		return label

	def update_tmp_labels(self, new_label_raw):
		new_label = self.make_label(new_label_raw, 48, 8)
		if not self.labels:
			self.labels = [ self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() ]
		if not self.labels[2]=='None':
			self.labels[3]='and more'
		self.labels[2] = self.labels[1]
		self.labels[1] = self.labels[0]
		self.labels[0] = new_label

	def show_tmp_labels(self):
		self.label_TempLine1.setText(self.labels[0])
		self.label_TempLine2.setText(self.labels[1])
		self.label_TempLine3.setText(self.labels[2])
		self.label_TempLine4.setText(self.labels[3])
		self.show()


	### changing screens
	@pyqtSlot()
	def to_template_screen(self):
		self.main = TemplateScreen(self.config, self.templatebank, self.data, self.labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_setup_screen(self):
		self.main = SetupScreen(self.config, self.templatebank, self.data, self.labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_data_screen(self):
		labels = [ self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() ]
		self.main = DataScreen(self.config, self.templatebank, self.data, labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_create_screen(self):
		labels = [ self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() ]
		self.main = CreateScreen(self.config, self.templatebank, self.data, labels)
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

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/template_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Template Management)')
		self.config = config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels
		if self.labels: self.show_tmp_labels()

		if self.config.getboolean('main', 'firststartup'): self.to_setup_screen()

		# connect Push Buttons
		self.pushButton_createTemplates.clicked.connect(self.to_create_screen)
		self.pushButton_loadDirectory.clicked.connect(self.load_directory)
		self.pushButton_loadFile.clicked.connect(self.load_file)
		self.pushButton_continue.clicked.connect(self.to_data_screen)

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_directory(self):
		path = self.getDirectoryDialog("Choose the directory to be loaded.", bankpath)
		self.templatebank.add_directory(path)
		self.update_tmp_labels(path)
		self.show_tmp_labels()
		return

	@pyqtSlot()
	def load_file(self):
		fullname = self.openFileNamesDialog()[0]
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.templatebank.add_template(path, filename)
		self.update_tmp_labels(fullname)
		self.show_tmp_labels()
		return



class SetupScreen(Screen):             # maybe this should be a QDialog instead of a Screen but it is like this now.

	def __init__(self, config, templatebank, data=None, labels=None):
		super().__init__(templatebank, labels)
		loadUi(cwd+'/setup_screen.ui', self)
		self.setWindowTitle('Matched Filtering with pycbc (Setup on first startup)')
		self.config = config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels

		# load the default config as main config
		self.config.set('main', 'os', self.config.get('default', 'os'))
		self.config.set('main', 'debugmode', self.config.get('default', 'debugmode'))
		self.config.set('main', 'bankpath', self.config.get('default', 'bankpath'))
		### to be removed:
		if self.config.get('main', 'debugmode'): self.config.set('main', 'bankpath', '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/05_pre-final-tests/matchedfilter_testfiles/templates/')


		# connect Push Buttons
		self.pushButton_chooseDir.clicked.connect(self.choose_dir)
		self.pushButton_done.clicked.connect(self.done)

		# set up radioButtons
		self.ButtonGroup_toggleOS = QButtonGroup()
		self.ButtonGroup_toggleOS.addButton(self.radioButton_windows, id=1)
		self.ButtonGroup_toggleOS.addButton(self.radioButton_linux, id=2)
		if self.config.get('default', 'os') == 'linux': 
			self.radioButton_linux.setChecked(True)
		else: 
			self.radioButton_windows.setChecked(True)
		self.ButtonGroup_toggleOS.buttonClicked.connect(self.toggleOS)
		self.ButtonGroup_toggleDebug = QButtonGroup()
		self.ButtonGroup_toggleDebug.addButton(self.radioButton_debugTrue, id=3)
		self.ButtonGroup_toggleDebug.addButton(self.radioButton_debugFalse, id=4)
		if self.config.getboolean('default', 'debugmode'):
			self.radioButton_debugTrue.setChecked(True)
		else:
			self.radioButton_debugFalse.setChecked(True)
		self.ButtonGroup_toggleDebug.buttonClicked.connect(self.toggleDebug)

	### methods connected with Push Buttons
	@pyqtSlot()
	def toggleOS(self):
		OS = 'windows'
		if self.ButtonGroup_toggleOS.checkedId() == 2:
			OS = 'linux'
		self.config.set('main', 'os', OS)
		return

	@pyqtSlot()
	def toggleDebug(self):
		debugmode = 'False'
		if self.ButtonGroup_toggleDebug.checkedId() == 3:
			debugmode = 'True'
		self.config.set('main', 'debugmode', debugmode)
		return

	@pyqtSlot()
	def choose_dir(self):
		path = self.getDirectoryDialog("Choose a directory for the template bank.", config.get('default', 'bankpath'))
		self.config.set('main', 'bankpath', path)
		return

	@pyqtSlot()
	def done(self):
		self.config.set('main', 'firststartup', 'False')
		with open('config.ini', 'w') as f:
			self.config.write(f)
		self.to_template_screen()
		return



class CreateScreen(Screen):

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/create_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Template Creation)')
		self.config = config
		self.templatebank = templatebank
		self.data = data
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
			self.label_FilenameExt.setText("+'Mr_[M]-[r]'")
			self.show()
			if debugmode: print('Mr')
		else:
			self.flag_Mr = False
			self.label_Parameter1.setText('mass 1 (m1)')
			self.label_Parameter2.setText('mass 2 (m2)')
			self.label_FilenameExt.setText("+'mm_[m1]-[m2]'")
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
		if self.flag_All:
			array = np.zeros( (2, len(array1)*len(array2)) )
			counter = 0
			for elem1 in array1:
				for elem2 in array2:
					array[0][counter] = elem1
					array[1][counter] = elem2
					counter += 1
		else:
			length = np.minimum( array1, array2 )
			array = np.asarray( (array1[:length], array2[:length]) )

		return array

	def create_templates(self):
		# We are following the example in the section "Using QThread to Prevent Freezing GUIs" from this website:
		# https://realpython.com/python-pyqt-qthread/
		
		# create QThread object
		self.thread = QThread()
		# gather input for Worker
		array = self.get_array()
		basename = self.lineEdit_FilenameBase.text() 
		freq_domain = self.checkBox_freq.isChecked()
		time_domain = self.checkBox_time.isChecked()
		# create Worker object and move it to thread
		self.worker = CreateTemplatesWorker(self.templatebank, array, self.path, basename, self.flag_Mr, freq_domain, time_domain)
		self.worker.moveToThread(self.thread)
		# connect signals and slots
		self.thread.started.connect(self.worker.create_templates)
		self.worker.finished.connect(self.thread.quit)
		self.worker.finished.connect(self.worker.deleteLater)
		self.thread.finished.connect(self.thread.deleteLater)
		# self.worker.progress.connect(self.reportProgress)   # has to be adjusted to my program
		# start the thread
		self.thread.start()

		# Final resets  ## these have to be adjusted to my program
		# self.longRunningBtn.setEnabled(False)
		# self.thread.finished.connect(
		# 	lambda: self.longRunningBtn.setEnabled(True)
		# )
		# self.thread.finished.connect(
		# 	lambda: self.stepLabel.setText("Long-Running Step: 0")
		# )

		self.update_tmp_labels(self.path)

	

class DataScreen(Screen):

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(templatebank, labels)
		loadUi(cwd+'/data_screen.ui',self)
		self.setWindowTitle('Matched Filtering with pycbc (Matched Filtering)')
		self.config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels
		# connect Push Buttons
		self.pushButton_loadData.clicked.connect(self.load_data)
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_go.clicked.connect(self.matched_filter)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		self.pushButton_plot_m1m2.clicked.connect(self.plot_results)
		self.pushButton_plot_Mr.clicked.connect(self.plot_results_Mr)
		# set Status
		if self.labels: self.show_tmp_labels()

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_data(self):
		fullname = self.openFileNameDialog("Open Data-File", "C:/Users/Praktikum/Desktop/LIGO")
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.data = handler.Data(path, filename)
		self.label_Data.setText( self.make_label(fullname, 35, 2) )
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
		# We are following the example in the section "Using QThread to Prevent Freezing GUIs" from this website:
		# https://realpython.com/python-pyqt-qthread/
		
		# create QThread object
		self.thread = QThread()
		# create Worker object and move it to thread
		self.worker = MatchedFilteringWorker(self.data, self.templatebank, connection)
		self.worker.moveToThread(self.thread)
		# connect signals and slots
		self.thread.started.connect(self.worker.matched_filter)
		self.worker.finished.connect(self.thread.quit)
		self.worker.finished.connect(self.worker.deleteLater)
		self.thread.finished.connect(self.thread.deleteLater)
		# self.worker.progress.connect(self.reportProgress)   # has to be adjusted to my program
		# start the thread
		self.thread.start()

		# Final resets  ## these have to be adjusted to my program
		# self.longRunningBtn.setEnabled(False)
		# self.thread.finished.connect(
		# 	lambda: self.longRunningBtn.setEnabled(True)
		# )
		# self.thread.finished.connect(
		# 	lambda: self.stepLabel.setText("Long-Running Step: 0")
		# )

	@pyqtSlot()
	def plot_results_Mr(self):
		self.plot_results(flag_Mr=True)

	@pyqtSlot()
	def plot_results(self, flag_Mr=False):
		# load results
		results_filename = self.data.savepath+'00_matched_filtering_results.dat'
		print(results_filename)
		results = np.loadtxt(results_filename,  dtype={'names': ('name', 'match', 'time', 'm1', 'm2', 'M', 'r'), 'formats': ('S5', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')})
		# shape arrays
		L = len(results)
		x = np.zeros(L)
		y = np.zeros(L)
		z = np.zeros(L)
		for index in range(L):
			x[index] = int(results[index][3])  # m1
			y[index] = int(results[index][4])  # m2
			z[index] = results[index][1]       # match
		# plot
		if flag_Mr:
			M = x+y
			r = x/y
			fig = plt.figure()
			ax = fig.add_subplot(projection='3d')
			ax.scatter(M,r,z)
			ax.set_xlabel('total mass')
			ax.set_ylabel('mass ratio')
			ax.set_zlabel('match')
		else:
			fig = plt.figure()
			ax = fig.add_subplot(projection='3d')
			ax.scatter(x,y,z)
			ax.set_xlabel('mass 1')
			ax.set_ylabel('mass 2')
			ax.set_zlabel('match')
		plt.show()


# General settings

config = ConfigParser()
config.read('config.ini')

cwd = os.getcwd()
mpi_path_host = cwd
mpi_path_container = '/input/mpi/'

connection = handler.connect()
templatebank = handler.TemplateBank()

### !!!!!!!!!!!!! could be removed in the end:     ## and it does not exactly work as intended now, as the main section does get altered after this call
if config.get('main', 'debugmode'): 
	connection.update_mpi(mpi_path_host, mpi_path_container)

# open Window
# -----------

with open('matchedfilter.qss','r') as qss:
	style = qss.read()

app = QApplication(sys.argv)
app.setStyleSheet(style)
win = TemplateScreen(config, templatebank)
win.show()
sys.exit(app.exec_())