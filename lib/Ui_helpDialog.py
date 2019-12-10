# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kim/Dropbox/programmation/gromoteur2019/trunk/lib/helpDialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_helpDialog(object):
    def setupUi(self, helpDialog):
        helpDialog.setObjectName("helpDialog")
        helpDialog.resize(1184, 958)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/images/gromoteurGmini.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        helpDialog.setWindowIcon(icon)
        helpDialog.setSizeGripEnabled(True)
        self.gridLayout_3 = QtWidgets.QGridLayout(helpDialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.tabWidget = QtWidgets.QTabWidget(helpDialog)
        self.tabWidget.setMaximumSize(QtCore.QSize(16777215, 555555))
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.West)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.helpWebView = QWebView(self.tab_3)
        self.helpWebView.setProperty("url", QtCore.QUrl("http://gromoteur.ilpga.fr"))
        self.helpWebView.setObjectName("helpWebView")
        self.gridLayout_4.addWidget(self.helpWebView, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.aboutTab = QtWidgets.QWidget()
        self.aboutTab.setObjectName("aboutTab")
        self.gridLayout = QtWidgets.QGridLayout(self.aboutTab)
        self.gridLayout.setObjectName("gridLayout")
        self.about = QtWidgets.QTextBrowser(self.aboutTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.about.sizePolicy().hasHeightForWidth())
        self.about.setSizePolicy(sizePolicy)
        self.about.setMaximumSize(QtCore.QSize(16777215, 55555))
        self.about.setOpenExternalLinks(True)
        self.about.setObjectName("about")
        self.gridLayout.addWidget(self.about, 0, 0, 1, 1)
        self.tabWidget.addTab(self.aboutTab, "")
        self.gnutab = QtWidgets.QWidget()
        self.gnutab.setObjectName("gnutab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.gnutab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gnulicence = QtWidgets.QTextBrowser(self.gnutab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gnulicence.sizePolicy().hasHeightForWidth())
        self.gnulicence.setSizePolicy(sizePolicy)
        self.gnulicence.setMaximumSize(QtCore.QSize(16777215, 55555))
        self.gnulicence.setObjectName("gnulicence")
        self.gridLayout_2.addWidget(self.gnulicence, 0, 0, 1, 1)
        self.tabWidget.addTab(self.gnutab, "")
        self.gridLayout_3.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(helpDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_3.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(helpDialog)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(helpDialog.accept)
        self.buttonBox.rejected.connect(helpDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(helpDialog)

    def retranslateUi(self, helpDialog):
        _translate = QtCore.QCoreApplication.translate
        helpDialog.setWindowTitle(_translate("helpDialog", "gromoteur help"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("helpDialog", "Getting started"))
        self.about.setHtml(_translate("helpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aboutTab), _translate("helpDialog", "About"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.gnutab), _translate("helpDialog", "GNU Licence"))

try: 	from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
except:	from PyQt5.QtWebKitWidgets import QWebView, QWebPage

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    helpDialog = QtWidgets.QDialog()
    ui = Ui_helpDialog()
    ui.setupUi(helpDialog)
    helpDialog.show()
    sys.exit(app.exec_())

