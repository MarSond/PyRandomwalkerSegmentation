from PyQt5 import QtCore
import numpy as np
from PyQt5.QtGui import QColor


def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)

class ImageLabel:
	LABEL_IDS = {'NONE': 0, 'BG': 1, 'CL1': 2, 'CL2': 3}
	color_bg: QColor = QColor('green')
	color_cl1: QColor = QColor('red')
	color_cl2: QColor = QColor('blue')
	LABEL_COLORS = {'1': color_bg, '2': color_cl1, '3': color_cl2}

	def __init__(self, dims):
		self.dims = dims
		self.label_map: np.ndarray = np.zeros(dims, dtype=np.int8)

	def unpaint(self, rect: QtCore.QRect):
		self.paint(self.LABEL_IDS['NONE'], rect)

	def paint(self, layer_id, rect: QtCore.QRect):
		if not layer_id in self.LABEL_IDS.values():
			print(str(layer_id) + " not in LayerList")
		else:
			tlX = rect.x()
			tlY = rect.y()
			brX = tlX + rect.width()
			brY = tlY + rect.height()
			print("Painting on Layer {}. TopLeft {},{} - BottomRight {},{}".format(layer_id, tlX, tlY, brX, brY))
			self.label_map[tlY:brY, tlX:brX] = layer_id

	def clear(self):
		self.label_map: np.ndarray = np.zeros(self.dims, dtype=np.int8)