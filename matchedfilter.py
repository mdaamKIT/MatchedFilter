#!/usr/bin/env python3

# This is the main-File.

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QButtonGroup, QMessageBox, QProgressDialog, QProgressBar
from PyQt5.uic import loadUi

import sys
import os
from configparser import ConfigParser
from ast import literal_eval
import numpy as np

from matplotlib.backends.backend_qtagg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


### worker objects for threading

class CreateTemplatesWorker(QThread):

	exceptionSignal = pyqtSignal()

	def __init__(self, templatebank, array, path, basename, attribute, freq_domain, time_domain):
		super().__init__()
		self.templatebank = templatebank
		self.array = array
		self.path = path
		self.basename = basename
		self.attribute = attribute
		self.freq_domain = freq_domain
		self.time_domain = time_domain

	def run(self):
		'Create templates from the user-input.'
		if not os.path.isdir(self.path): 
			errorstring = 'Output path not found.\n'
			raise NotADirectoryError(errorstring)
		else:
			try:
				self.templatebank.create_templates(self.array, self.path, self.basename, self.attribute, self.freq_domain, self.time_domain)
			except:
				self.exceptionSignal.emit()


class MatchedFilteringWorker(QThread):

	exceptionSignal = pyqtSignal()

	def __init__(self, data, templatebank, debugmode):
		super().__init__()
		self.data = data
		self.templatebank = templatebank
		self.OS = OS
		self.debugmode = debugmode

	def run(self):
		try:
			self.data.matched_filter(self.templatebank, self.debugmode)
		except:
			self.exceptionSignal.emit()


class Canvas3DPlot(QMainWindow):

	def __init__(self, results, attribute='individual', parent=None):
		super().__init__(parent)

		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.setCentralWidget(self.canvas)
		self.addToolBar(Qt.TopToolBarArea, NavigationToolbar(self.canvas, self)) # needed?

		# shape arrays
		L = len(results)
		x = np.zeros(L)
		y = np.zeros(L)
		z = np.zeros(L)
		for index in range(L):
			x[index] = results[index][3]    # m1
			y[index] = results[index][4]    # m2
			z[index] = results[index][1]    # match

		# plot
		self.ax = self.figure.subplots(subplot_kw=dict(projection='3d'))
		if attribute == 'total':
			M = x+y
			r = y/x
			self.ax.scatter(M,r,z, color='tab:purple')
			self.ax.set_xlabel('total mass')
			self.ax.set_ylabel('mass ratio')
			self.ax.set_zlabel('match')
		elif attribute == 'chirp':
			Mc = np.power(np.power(x*y, 3)/(x+y), 0.2)
			r = y/x
			self.ax.scatter(Mc,r,z, color='tab:purple')
			self.ax.set_xlabel('chirp mass')
			self.ax.set_ylabel('mass ratio')
			self.ax.set_zlabel('match')
		else:
			self.ax.scatter(x,y,z, color='tab:purple')
			self.ax.set_xlabel('mass 1')
			self.ax.set_ylabel('mass 2')
			self.ax.set_zlabel('match')
		self.canvas.draw_idle()


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
		# settings for label length
		self.label_maxlen = 48
		self.label_indent = 8
	

	### label handling
	def make_label(self, string, maxlen, indent):
		'Cut a string from the start so it does not exceed maxlen, even with dots and indentation.'
		label = string
		if len(label) > (maxlen-indent):
			label = '...'+label[-(maxlen-indent-3):]
		label = ' '*indent+label
		return label

	def update_tmp_labels(self, new_label_raw):
		new_label = self.make_label(new_label_raw, self.label_maxlen, self.label_indent)
		if not self.labels:
			self.labels = [ self.label_TempLine1.text(), self.label_TempLine2.text(), self.label_TempLine3.text(), self.label_TempLine4.text() ]
		if not self.labels[2]=='        None':
			self.labels[3]='and more'
		self.labels[2] = self.labels[1]
		self.labels[1] = self.labels[0]
		self.labels[0] = new_label

	def show_tmp_labels(self):
		try:
			self.label_TempLine1.setText(self.labels[0])
			self.label_TempLine2.setText(self.labels[1])
			self.label_TempLine3.setText(self.labels[2])
			self.label_TempLine4.setText(self.labels[3])
		except:
			raise
		self.show()


	### changing screens
	@pyqtSlot()
	def to_template_screen(self):
		self.main = TemplateScreen(self.config, self.templatebank, self.data, self.labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_setup_screen(self): # not necessary anymore
		self.main = SetupScreen(self.config, self.templatebank, self.data, self.labels)
		self.main.show()
		self.close()

	@pyqtSlot()
	def to_data_screen(self):
		stay = False
		if len(self.templatebank.list_of_templates)==0:
			answer = QMessageBox.question(
				self,
				"No templates have been loaded", 
				'It seems, you did not load any templates in the template management.\n\nDo you want to continue anyway?',
				QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
				)
			if answer==QMessageBox.StandardButton.No:
				stay = True
		if not stay:
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

	def openFileNameDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self, DialogName, defaultpath ,"All Files (*);;Python Files (*.py)", options=options)
		if not fileName:
			print('No file selected.')
		else:
			return fileName

	def openFileNamesDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self, DialogName, defaultpath ,"All Files (*);;Python Files (*.py)", options=options)
		if not files:
			print('No files selected.')
		else:
			return files

	def getDirectoryDialog(self, DialogName, defaultpath):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		options |= QFileDialog.ShowDirsOnly
		dirName = QFileDialog.getExistingDirectory(self, DialogName, defaultpath, options=options)
		if not dirName:
			print('No directory selected.')
		else:
			return dirName+'/'



class TemplateScreen(Screen):

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(config, templatebank, labels)
		loadUi(os.getcwd()+'/template_screen.ui',self)
		self.setWindowTitle('Matched filtering with pycbc (template management)')
		self.config = config
		if isinstance(templatebank, handler.TemplateBank):
			self.templatebank = templatebank
		else:
			self.templatebank = handler.TemplateBank()			
		self.data = data
		self.labels = labels
		if self.labels: self.show_tmp_labels()

		# connect Push Buttons
		self.pushButton_createTemplates.clicked.connect(self.to_create_screen)
		self.pushButton_loadDirectory.clicked.connect(self.load_directory)
		self.pushButton_loadFile.clicked.connect(self.load_file)
		self.pushButton_continue.clicked.connect(self.to_data_screen)

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_directory(self):
		path = self.getDirectoryDialog("Choose the directory to load templates from", self.config.get('main', 'bankpath'))
		if path:
			self.templatebank.add_directory(path)
			self.update_tmp_labels(path)
			self.show_tmp_labels()
			self.config.set('main', 'bankpath', os.path.dirname(os.path.normpath(path))+'/')
			with open('config.ini', 'w') as f:
				self.config.write(f)
		return

	@pyqtSlot()
	def load_file(self):
		filenames = self.openFileNamesDialog("Open template-file(s)", self.config.get('main', 'bankpath'))
		for fullname in filenames:
			if fullname:
				path = os.path.dirname(fullname)+'/'
				filename = os.path.basename(fullname)
				self.templatebank.add_template(path, filename)
				self.update_tmp_labels(fullname)
		self.show_tmp_labels()
		return



class SetupScreen(Screen):             # maybe this should be a QDialog instead of a Screen but it is like this now.

	def __init__(self, config, templatebank, data=None, labels=None):
		super().__init__(config, templatebank, labels)
		loadUi(os.getcwd()+'/setup_screen.ui', self)
		self.setWindowTitle('Matched filtering with pycbc (Setup on first startup)')
		self.config = config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels

		# load the default config as main config
		self.config.set('main', 'os', self.config.get('default', 'os'))
		self.config.set('main', 'debugmode', self.config.get('default', 'debugmode'))
		self.config.set('main', 'bankpath', self.config.get('default', 'bankpath'))
		self.config.set('main', 'datapath', self.config.get('default', 'datapath'))
		### to be removed:
		if self.config.getboolean('main', 'debugmode'): self.config.set('main', 'bankpath', '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/05_pre-final-tests/matchedfilter_testfiles/templates/')

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
		path = self.getDirectoryDialog("Choose a directory to store templates.", self.config.get('default', 'bankpath'))
		if path:
			self.config.set('main', 'bankpath', path)
		return

	@pyqtSlot()
	def done(self):
		self.config.set('main', 'firststartup', 'False')
		OS = self.config.get('main', 'os')
		if OS=='windows':
			import templatebank_handler_win as handler
		elif OS=='linux':
			import templatebank_handler_linux as handler
		else:
			raise ValueError('''Value for os in [main] in config.ini is expected to be either 'windows' or 'linux', but I got: ''', OS)
		with open('config.ini', 'w') as f:
			self.config.write(f)
		self.to_template_screen()
		return



class CreateScreen(Screen):

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(config, templatebank, labels)
		loadUi(os.getcwd()+'/create_screen.ui',self)
		self.setWindowTitle('Matched filtering with pycbc (template creation)')
		self.config = config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels
		self.attribute = 'individual'
		self.flag_All = True
		self.path = self.config.get('main', 'bankpath')
		self.label_path.setText(self.path)
		# connect pushButtons
		self.pushButton_chirpmass.clicked.connect(self.chirpmass_info)
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_create.clicked.connect(self.create_templates)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		# set up radioButtons
		self.ButtonGroup_Attribute = QButtonGroup()
		self.ButtonGroup_Attribute.addButton(self.radioButton_individual, id=1)
		self.ButtonGroup_Attribute.addButton(self.radioButton_total, id=2)
		self.ButtonGroup_Attribute.addButton(self.radioButton_chirp, id=3)
		self.radioButton_individual.setChecked(True)
		self.ButtonGroup_Attribute.buttonClicked.connect(self.change_Attribute)
		self.ButtonGroup_All = QButtonGroup()
		self.ButtonGroup_All.addButton(self.radioButton_AllOn, id=4)
		self.ButtonGroup_All.addButton(self.radioButton_AllOff, id=5)
		self.radioButton_AllOn.setChecked(True)
		self.ButtonGroup_All.buttonClicked.connect(self.change_All)
		# set up checkBoxes
		self.checkBox_Para1Code.setChecked(False)
		self.checkBox_Para2Code.setChecked(False)
		self.checkBox_freq.setChecked(True)
		self.checkBox_time.setChecked(False)

	@pyqtSlot()
	def chirpmass_info(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("Chirp Mass")
		msg.setInformativeText('The quantity chirp mass is a good mass parameter to describe the gravitational wave in most cases. '+
			'It is defined by: \n\n'+
			'Mc = [(m1*m2)^3/(m1+m2)]^(1/5).\n\n'+
			'Analyzing your signals, you will probably find that the best matching templates often share the same chirp mass.')
		msg.setWindowTitle("Information: chirp mass")
		msg.exec_()

	@pyqtSlot()
	def change_output(self):
		self.path = self.getDirectoryDialog('Choose the new output directory.', self.path)
		if self.path:
			self.label_path.setText(self.make_label(self.path,100,0))
			self.show()
			self.config.set('main', 'bankpath', os.path.dirname(os.path.normpath(self.path))+'/')
			with open('config.ini', 'w') as f:
				self.config.write(f)
		return

	@pyqtSlot()
	def change_Attribute(self):
		'Change the Layout and keyword attribute, if one of the Attribute radioButtons is clicked.'
		if self.ButtonGroup_Attribute.checkedId() == 1:
			self.attribute = 'individual'
			self.label_Parameter1.setText('mass 1 (m1)')
			self.label_Parameter2.setText('mass 2 (m2)')
			self.label_FilenameExt.setText("+'mm_[m1]-[m2]'")
			self.show()
		elif self.ButtonGroup_Attribute.checkedId() == 2:
			self.attribute = 'total'
			self.label_Parameter1.setText('total mass (M)')
			self.label_Parameter2.setText('mass ratio (R)')
			self.label_FilenameExt.setText("+'MR_[M]-[R]'")
			self.show()
		elif self.ButtonGroup_Attribute.checkedId() == 3:
			self.attribute = 'chirp'
			self.label_Parameter1.setText('chirp mass (Mc)')
			self.label_Parameter2.setText('mass ratio (R)')
			self.label_FilenameExt.setText("+'McR_[Mc]-[R]'")
			self.show()
		else:
			raise ValueError('Unexpected behaviour of the ButtonGroup_Attribute: self.ButtonGroup_Attribute.checkedId() = ',self.ButtonGroup_Attribute.checkedId())

	@pyqtSlot()
	def change_All(self):
		'Change the Layout and flag_All, if one of the All radioButtons is clicked.'
		if self.ButtonGroup_All.checkedId() == 4:
			self.flag_All = True
		else:
			self.flag_All = False

	def get_array(self):
		'Convert input from the lineEdit fields into the appropriate 2d numpy array.'

		# get first sub-array
		if self.checkBox_Para1Code.isChecked():
			array1 = literal_eval(self.lineEdit_Para1Code.text())
		else:
			start1 = float(literal_eval(self.lineEdit_Para1Start.text()))
			stop1 = float(literal_eval(self.lineEdit_Para1Stop.text()))
			num1 = int(literal_eval(self.lineEdit_Para1Number.text()))
			array1 = np.linspace(start1,stop1, num=num1, endpoint=True)
		
		# get second sub-array
		if self.checkBox_Para2Code.isChecked():
			array2 = literal_eval(self.lineEdit_Para2Code.text())
		else:			
			start2 = float(literal_eval(self.lineEdit_Para2Start.text()))
			stop2 = float(literal_eval(self.lineEdit_Para2Stop.text()))
			num2 = int(literal_eval(self.lineEdit_Para2Number.text()))
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

		# gather input for Worker
		array = self.get_array()
		basename = self.lineEdit_FilenameBase.text() 
		freq_domain = self.checkBox_freq.isChecked()
		time_domain = self.checkBox_time.isChecked()

		# set up the progress_dialog
		self.progress_dialog = QProgressDialog("Preparing template creation,\n please wait...", "Cancel", 0, len(array[0])+1, self) # None instead of "Cancel" as CancelButtonText removes the cancel-button.
		self.progress_dialog.canceled.connect(self.create_cancel)
		self.progress_bar = QProgressBar(self.progress_dialog)
		self.progress_bar.setMaximum(len(array[0])+1)
		self.progress_dialog.setBar(self.progress_bar)
		self.progress_dialog.setWindowTitle("Create templates")
		self.progress_dialog.setWindowModality(Qt.WindowModal)
		# self.progress_dialog.canceled.connect(self.create_stop)  # for some reason this line triggers the mf_stop also when the progress_dialog.close gets called.

		# create worker Thread
		self.worker = CreateTemplatesWorker(self.templatebank, array, self.path, basename, self.attribute, freq_domain, time_domain)
		self.worker.exceptionSignal.connect(self.create_exception)
		self.worker.finished.connect(self.create_stop)
		self.worker.start()

		# setup timer to update the progress_dialog		
		self.timer = QTimer()
		self.timer.timeout.connect(self.create_update_progress)
		self.timer.start(1000)  # in ms - 1000 means the progress_bar gets updated once every second

	def create_update_progress(self):
		if os.path.isfile(self.path+'00_progress_create.dat'):
			track_progress = np.loadtxt(self.path+'00_progress_create.dat', dtype=int)
			if len(track_progress)==2:
				self.progress_dialog.setLabelText("creating templates...")
				self.progress_bar.setMaximum(track_progress[1])
				self.progress_dialog.setValue(track_progress[0])
				if track_progress[0]==track_progress[1]:
					self.timer.stop()

	def create_cancel(self, event=None):
		canceled = np.ones(1, dtype=bool)
		canceled.tofile(self.path+'canceled.txt') # read as np.fromfile(self.path+'canceled.txt', dtype=bool)
		self.timer.stop()
		self.progress_dialog.close()
		self.worker.wait()
		self.worker.deleteLater()
		try:
			os.remove(self.path+'canceled.txt')
		except FileNotFoundError:
			pass
		return

	def create_stop(self, event=None):
		self.timer.stop()
		self.progress_dialog.close()
		self.worker.wait()
		self.worker.deleteLater()
		if os.path.isfile(self.path+'00_progress_create.dat'):
			try:
				os.remove(self.path+'00_progress_create.dat')
			except PermissionError:
				print('No permission to remove 00_progress_mf.dat. Moving on.')
		self.update_tmp_labels(self.path+' (new templates)')

	def create_exception(self):
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Error: no templates created")
			msg.setInformativeText('Most probably the docker engine is not running.\n\nTry the follwing steps:\n 1. Close this application.\n 2. Start the Docker Desktop application.\n 3. Start this application again.')
			msg.setWindowTitle("Error")
			msg.exec_()
			print()
			print('Something went wrong while trying to create templates. Most probably the docker engine is not running.')

	

class DataScreen(Screen):

	def __init__(self, config, templatebank, data=None, labels=None):
		# general settings and initiation of ui
		super().__init__(config, templatebank, labels)
		loadUi(os.getcwd()+'/data_screen.ui',self)
		self.setWindowTitle('Matched filtering with pycbc (matched filtering)')
		self.config
		self.templatebank = templatebank
		self.data = data
		self.labels = labels
		# connect Push Buttons
		self.pushButton_loadData.clicked.connect(self.load_data)
		self.pushButton_changeOutput.clicked.connect(self.change_output)
		self.pushButton_go.clicked.connect(self.matched_filter)
		self.pushButton_back.clicked.connect(self.to_template_screen)
		self.pushButton_plot.clicked.connect(self.plot_results)
		# set up Radio Buttons
		self.ButtonGroup_Attribute = QButtonGroup()
		self.ButtonGroup_Attribute.addButton(self.radioButton_mm, id=1)
		self.ButtonGroup_Attribute.addButton(self.radioButton_MR, id=2)
		self.ButtonGroup_Attribute.addButton(self.radioButton_McR, id=3)
		self.radioButton_mm.setChecked(True)
		# set Status
		if self.labels: self.show_tmp_labels()

	### methods connected with Push Buttons
	@pyqtSlot()
	def load_data(self):
		fullname = self.openFileNameDialog("Open Data-File", self.config.get('main', 'datapath'))
		if fullname:
			path = os.path.dirname(fullname)+'/'
			self.config.set('main', 'datapath', path)
			with open('config.ini', 'w') as f:
				self.config.write(f)
			filename = os.path.basename(fullname)
			self.data = handler.Data(path, filename)
			self.label_Data.setText( self.make_label(fullname, 35, 2) )
			self.label_Output.setText( self.make_label(self.data.savepath,35,2) )
			self.show()
		return

	@pyqtSlot()
	def change_output(self):
		newpath = self.getDirectoryDialog('Choose the new output directory.', self.data.datapath)
		if newpath:
			self.data.set_savepath(newpath)
			self.label_Output.setText( self.make_label(self.data.savepath,35,2) )
			self.show()
		return

	@pyqtSlot()
	def matched_filter(self):

		if isinstance(self.data, handler.Data):

			# make sure, matched filtering can be started (prevents overriding of existing results)
			do_mf = True
			if os.path.isfile(self.data.savepath+'00_matched_filtering_results.dat'):
				do_mf = False
				answer = QMessageBox.question(
					self,
					"Overwrite existing results?", 
					'The chosen output directory already contains the results of a previous matched filtering.\n\nDo you want to continue and overwrite the existing results?',
					QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
					)
				if answer==QMessageBox.StandardButton.Yes:
					do_mf = True

			# start matched filtering
			if do_mf:
				# set up the progress_dialog
				self.progress_dialog = QProgressDialog("Preparing matched filtering,\n please wait...", "Cancel", 0, len(self.templatebank.list_of_templates)+2, self) # None instead of "Cancel" as CancelButtonText removes the cancel-button.
				self.progress_dialog.canceled.connect(self.mf_cancel)
				self.progress_bar = QProgressBar(self.progress_dialog)
				self.progress_bar.setMaximum(len(self.templatebank.list_of_templates)+2)
				self.progress_dialog.setBar(self.progress_bar)
				self.progress_dialog.setWindowTitle("Matched filtering")
				self.progress_dialog.setWindowModality(Qt.WindowModal)
				# self.progress_dialog.canceled.connect(self.mf_stop)  # for some reason this line triggers the mf_stop also when the progress_dialog.close gets called.

				# create worker Thread
				self.worker = MatchedFilteringWorker(self.data, self.templatebank, self.config.getboolean('main', 'debugmode'))
				self.worker.exceptionSignal.connect(self.mf_exception)
				self.worker.finished.connect(self.mf_stop)
				self.worker.start()

				# setup timer to update the progress_dialog		
				self.timer = QTimer()
				self.timer.timeout.connect(self.mf_update_progress)
				self.timer.start(1000)  # in ms - 1000 means the progress_bar gets updated once every second

		else:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Error: no data object")
			msg.setInformativeText('You need to load data before executing matched filtering.')
			msg.setWindowTitle("Error")
			msg.exec_()


	def mf_update_progress(self):
		if os.path.isfile(self.data.savepath+'00_progress_mf.dat'):
			track_progress = np.loadtxt(self.data.savepath+'00_progress_mf.dat', dtype=int)
			if len(track_progress)==2:
				self.progress_dialog.setLabelText("matched filtering in progress...")
				self.progress_bar.setMaximum(track_progress[1])
				self.progress_dialog.setValue(track_progress[0])
				if track_progress[0]==track_progress[1]:
					self.timer.stop()

	def mf_cancel(self):
		canceled = np.ones(1, dtype=bool)
		canceled.tofile(self.data.savepath+'canceled.txt') # read as np.fromfile(self.path+'canceled.txt', dtype=bool)
		self.timer.stop()
		self.progress_dialog.close()
		self.worker.wait()
		self.worker.deleteLater()
		try:
			os.remove(self.data.savepath+'canceled.txt')
		except FileNotFoundError:
			pass
		return

	def mf_stop(self, event=None):
		self.timer.stop()
		self.progress_dialog.close()
		self.worker.wait()
		self.worker.deleteLater()
		if os.path.isfile(self.data.savepath+'00_progress_create.dat'):
			try:
				os.remove(self.data.savepath+'00_progress_mf.dat')
			except FileNotFoundError:
				pass
			except PermissionError:
				print('No permission to remove 00_progress_mf.dat. Moving on.')

	def mf_exception(self):
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Error: no matched filtering done")
			msg.setInformativeText('Most probably the docker engine is not running.\n\nTry the follwing steps:\n 1. Close this application.\n 2. Start the Docker Desktop application.\n 3. Start this application again.')
			msg.setWindowTitle("Error")
			msg.exec_()
			print()
			print('Something went wrong while trying to execute the matched filtering. Most probably the docker engine is not running.')

	@pyqtSlot()
	def plot_results(self, flag_Mr=False):

		if isinstance(self.data, handler.Data):

			# check which radioButton is checked and set keyword attribute
			attribute = 'individual'
			if self.ButtonGroup_Attribute.checkedId() == 2:
				attribute = 'total'
			elif self.ButtonGroup_Attribute.checkedId() == 3:
				attribute = 'chirp'
			elif self.ButtonGroup_Attribute.checkedId() != 1:
				raise ValueError('Unexpected behaviour of the ButtonGroup_Attribute: self.ButtonGroup_Attribute.checkedId() = ',self.ButtonGroup_Attribute.checkedId())

			# load results
			results_filename = self.data.savepath+'00_matched_filtering_results.dat'
			if os.path.isfile(results_filename): 														# should I better do this in try/except style?
				results = np.loadtxt(results_filename,  dtype={'names': ('name', 'match', 'time', 'm1', 'm2', 'M', 'r', 'Mc'), 'formats': ('S5', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')})
				self.canvas = Canvas3DPlot(results, attribute)
				self.canvas.show()

			else:
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Error: no results to plot")
				msg.setInformativeText('You need to execute matched filtering before trying to plot results.')
				msg.setWindowTitle("Error")
				msg.exec_()

		else:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Error: no data object")
			msg.setInformativeText('You need to load Data and execute matched filtering before trying to plot results.')
			msg.setWindowTitle("Error")
			msg.exec_()





# open Window
# -----------

config = ConfigParser()
config.read('config.ini')

OS = config.get('main', 'os')
if OS=='windows':
	import templatebank_handler_win as handler
elif OS=='linux':
	import templatebank_handler_linux as handler
else:
	raise ValueError('''Value for os in [main] in config.ini is expected to be either 'windows' or 'linux', but I got: ''', OS)

with open('matchedfilter.qss','r') as qss:
	style = qss.read()

app = QApplication(sys.argv)
app.setStyleSheet(style)
win = TemplateScreen(config, None, None)
if config.getboolean('main', 'firststartup'): win = SetupScreen(config, None, None)
win.show()
sys.exit(app.exec_())