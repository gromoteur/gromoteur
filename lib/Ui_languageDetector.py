# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kim/Dropbox/programmation/gromoteur2019/trunk/lib/languageDetector.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_languageDialog(object):
    def setupUi(self, languageDialog):
        languageDialog.setObjectName("languageDialog")
        languageDialog.resize(1059, 829)
        self.gridLayout_3 = QtWidgets.QGridLayout(languageDialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.buttonBox = QtWidgets.QDialogButtonBox(languageDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_3.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.splitter = QtWidgets.QSplitter(languageDialog)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.groupBox = QtWidgets.QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.learnButton = QtWidgets.QPushButton(self.groupBox)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/images/languageDetector.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.learnButton.setIcon(icon)
        self.learnButton.setObjectName("learnButton")
        self.gridLayout.addWidget(self.learnButton, 0, 5, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 3, 1, 1)
        self.newlanguagecodelineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.newlanguagecodelineEdit.setObjectName("newlanguagecodelineEdit")
        self.gridLayout.addWidget(self.newlanguagecodelineEdit, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.ngramtableWidget = QtWidgets.QTableWidget(self.groupBox)
        self.ngramtableWidget.setObjectName("ngramtableWidget")
        self.ngramtableWidget.setColumnCount(0)
        self.ngramtableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.ngramtableWidget, 1, 5, 1, 1)
        self.languageDetectorLabel = QtWidgets.QLabel(self.groupBox)
        self.languageDetectorLabel.setText("")
        self.languageDetectorLabel.setObjectName("languageDetectorLabel")
        self.gridLayout.addWidget(self.languageDetectorLabel, 2, 1, 1, 1)
        self.newlanguagenamelineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.newlanguagenamelineEdit.setObjectName("newlanguagenamelineEdit")
        self.gridLayout.addWidget(self.newlanguagenamelineEdit, 0, 4, 1, 1)
        self.trainTextEdit = QtWidgets.QPlainTextEdit(self.groupBox)
        self.trainTextEdit.setObjectName("trainTextEdit")
        self.gridLayout.addWidget(self.trainTextEdit, 1, 0, 1, 5)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.splitter)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.testTextEdit = QtWidgets.QPlainTextEdit(self.groupBox_2)
        self.testTextEdit.setObjectName("testTextEdit")
        self.gridLayout_2.addWidget(self.testTextEdit, 0, 0, 1, 1)
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox_2)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout_2.addWidget(self.tableWidget, 0, 1, 2, 1)
        self.gridLayout_3.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(languageDialog)
        self.buttonBox.accepted.connect(languageDialog.accept)
        self.buttonBox.rejected.connect(languageDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(languageDialog)

    def retranslateUi(self, languageDialog):
        _translate = QtCore.QCoreApplication.translate
        languageDialog.setWindowTitle(_translate("languageDialog", "languages"))
        self.groupBox.setTitle(_translate("languageDialog", "train ngrams"))
        self.learnButton.setText(_translate("languageDialog", "learn (create ngrams)"))
        self.label.setText(_translate("languageDialog", "language name:"))
        self.newlanguagecodelineEdit.setText(_translate("languageDialog", "xx"))
        self.label_2.setText(_translate("languageDialog", "language code"))
        self.newlanguagenamelineEdit.setWhatsThis(_translate("languageDialog", "<html><head/><body><p>language name</p></body></html>"))
        self.newlanguagenamelineEdit.setText(_translate("languageDialog", "newspeak"))
        self.trainTextEdit.setPlainText(_translate("languageDialog", "paste some sample text of the new language here"))
        self.groupBox_2.setTitle(_translate("languageDialog", "test"))
        self.testTextEdit.setPlainText(_translate("languageDialog", "paste some text here for testing the language detection"))


#import groressources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    languageDialog = QtWidgets.QDialog()
    ui = Ui_languageDialog()
    ui.setupUi(languageDialog)
    languageDialog.show()
    sys.exit(app.exec_())
