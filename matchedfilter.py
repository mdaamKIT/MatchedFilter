#!/usr/bin/python3

# This is the main-File.

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.uic import loadUi

import sys
import os
import templatebank_handler as handler  # selfmade; defines classes for matched filtering

debugmode = True

# I guess I could get rid of the "debug-methods"? Or at least change them.


class SoundofMI(QMainWindow):

	# set defaults
	cwd = os.getcwd()
	defaultbankpath = 'C:/Users/Praktikum/Desktop/LIGO/template_bank/'
	templatebank = handler.TemplateBank()
	
	def __init__(self):
	    ### general settings and initiation of ui
	    super(SoundofMI,self).__init__()
	    loadUi(SoundofMI.cwd+'/matchedfilter.ui',self)
	    self.setWindowTitle('Matched Filtering with pycbc')
	    ## initiate Push Buttons
	    # 1 input section
	    self.pushButton_loadsignal.clicked.connect(self.loadsignal)
	    # 2a Matched Filtering with template bank section
	    self.pushButton_loadbank.clicked.connect(self.loadbank)
	    self.pushButton_loadtemplate.clicked.connect(self.loadtemplate)
	    self.pushButton_tbchangepath.clicked.connect(self.changetbsavepath)
	    self.pushButton_bank.clicked.connect(self.bankcheck)
	    # 2b Matched Filtering with single file
	    self.pushButton_stchangepath.clicked.connect(self.changestsavepath)
	    self.pushButton_single.clicked.connect(self.singlecheck)
	    ## initiate feedback for user
	    if debugmode:
	    	self.label_showstatus.setText('ready')
	    	self.show()
	    	print('<<< ready >>>')

	### debug-methods (feedback for user)
	def beginmethod(self, name):
		if debugmode:
			self.label_showstatus.setText('evaluating')
			self.label_showtask.setText(name)
			self.show()
			print('----------------')
			print('### >'+name+'< started... ###')
			print('----')
		return

	def begintask(self, name):
		if debugmode:
			self.label_showstatus.setText('evaluating')
			self.label_showtask.setText(name)
			self.show()
			print('>started: '+name)
		return

	def endtask(self, name):
		if debugmode:
			self.label_showstatus.setText('ready')
			self.label_showtask.setText('no task')
			self.show()
			print('>completed: '+name+'<')
			print('----')
		return

	def endmethod(self, name):
		if debugmode:
			self.label_showstatus.setText('ready')
			self.label_showtask.setText('no task')
			self.show()
			print('### >'+name+'< succesful. ###')
			print('----------------')
			print('<<< ready >>>')
		return

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
		files, _ = QFileDialog.getOpenFileNames(self,"Open Template-File(s)", "C:/Users/Praktikum/Desktop/LIGO/template_bank","All Files (*);;Python Files (*.py)", options=options)
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
	def loadsignal(self):
		methodname = 'load signal'
		self.beginmethod(methodname)
		fullname = self.openFileNameDialog("Open Signal-File", "C:/Users/Praktikum/Desktop/LIGO")
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.dataobj = handler.Data(path, filename)
		self.label_sigfile.setText(fullname)
		self.label_evastatus.setText('Loaded signal: '+filename)
		self.label_evastatus_2.setText('Loaded signal: '+filename)
		self.label_tboutpath.setText(self.dataobj.parentpath)
		self.lineEdit_tbcaption.setText(filename[:-4])
		self.label_stoutpath.setText(self.dataobj.parentpath)
		self.lineEdit_stcaption.setText(filename[:-4])
		self.show()
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def loadbank(self):
		methodname = 'load directory'
		self.beginmethod(methodname)
		path = self.getDirectoryDialog("Choose the directory to be loaded.", self.defaultbankpath)
		self.templatebank.add_directory(path)
		if not self.label_dir2.text()=='None':
			self.label_dirmore.setText('and more')
		self.label_dir2.setText(self.label_dir1.text())
		self.label_dir1.setText(self.label_dir0.text())
		self.label_dir0.setText(path)
		self.show()
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def loadtemplate(self):
		methodname = 'load single template'
		self.beginmethod(methodname)
		fullname = self.openFileNamesDialog()[0]
		print(fullname)
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		self.templatebank.add_template(path, filename)
		if not self.label_tmp2.text()=='None':
			self.label_tmpmore.setText('and more')
		self.label_tmp2.setText(self.label_tmp1.text())
		self.label_tmp1.setText(self.label_tmp0.text())
		self.label_tmp0.setText(filename)
		self.show()
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def changetbsavepath(self):
		methodname = 'change output path'
		self.beginmethod(methodname)
		newpath = self.getDirectoryDialog('Choose the new output directory.', self.dataobj.parentpath)
		self.label_tboutpath.setText(newpath)
		self.show()
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def bankcheck(self):
		methodname = 'matched filtering with template bank'
		self.beginmethod(methodname)
		self.dataobj.setparentpath(self.label_tboutpath.text())
		self.dataobj.setshortname(self.lineEdit_tbcaption.text())
		self.dataobj.check_bank(self.templatebank)
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def changestsavepath(self):
		methodname = 'change output path'
		self.beginmethod(methodname)
		newpath = self.getDirectoryDialog('Choose the new output directory.', self.dataobj.parentpath)
		self.label_stoutpath.setText(newpath)
		self.show()
		self.endmethod(methodname)
		return

	@pyqtSlot()
	def singlecheck(self):
		methodname = 'matched filtering with single template'
		self.beginmethod(methodname)
		fullname = self.openFileNameDialog('Choose Template File.', self.defaultbankpath)
		path = os.path.dirname(fullname)+'/'
		filename = os.path.basename(fullname)
		taskname = 'load template ('+filename+')'
		self.begintask(taskname)
		self.tmpobj = handler.Template(path, filename)
		self.endtask(taskname)
		self.dataobj.setparentpath(self.label_stoutpath.text())
		self.dataobj.setshortname(self.lineEdit_stcaption.text())
		self.dataobj.check_template(self.tmpobj)
		self.endmethod(methodname)
		return


# open Window
# -----------

with open('matchedfilter.qss','r') as qss:
	style = qss.read()

app = QApplication(sys.argv)
app.setStyleSheet(style)
win = SoundofMI()
win.show()
sys.exit(app.exec_())