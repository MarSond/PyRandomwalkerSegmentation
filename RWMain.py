from PyQt5 import QtWidgets
from GUI import ui_main

if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	window = ui_main.UI_MainWindow()
	app.exec_()
