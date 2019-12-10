# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kim/Dropbox/programmation/gromoteur2019/trunk/lib/importer.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Importer(object):
    def setupUi(self, Importer):
        Importer.setObjectName("Importer")
        Importer.resize(400, 300)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/images/gro.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Importer.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(Importer)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(Importer)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Importer)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/images/images/alert.png"))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.message = QtWidgets.QLabel(Importer)
        self.message.setObjectName("message")
        self.horizontalLayout.addWidget(self.message)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(Importer)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 1, 0, 1, 1)

        self.retranslateUi(Importer)
        self.buttonBox.accepted.connect(Importer.accept)
        self.buttonBox.rejected.connect(Importer.reject)
        QtCore.QMetaObject.connectSlotsByName(Importer)

    def retranslateUi(self, Importer):
        _translate = QtCore.QCoreApplication.translate
        Importer.setWindowTitle(_translate("Importer", "File Importer"))
        self.message.setText(_translate("Importer", "Are you sure?"))

#import groressources_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Importer = QtWidgets.QDialog()
    ui = Ui_Importer()
    ui.setupUi(Importer)
    Importer.show()
    sys.exit(app.exec_())

