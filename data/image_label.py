from PyQt5.QtCore import QRect
import numpy as np
from PyQt5.QtGui import QColor


def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)


class ImageLabel:
	# Each label class gets an own ID as an integer for representation in matrices
	# Color of each label is determined here, so that every module can access it with no confusion.
	LABEL_IDS = {'NONE': 0, 'BG': 1, 'CL1': 2, 'CL2': 3}
	color_bg: QColor = QColor('green')
	color_cl1: QColor = QColor('red')
	color_cl2: QColor = QColor('blue')
	LABEL_COLORS = {'1': color_bg, '2': color_cl1, '3': color_cl2}

	def __init__(self, dims):
		self.dims = dims
		self.label_map: np.ndarray = np.zeros(dims, dtype=np.int8)

	def unpaint(self, rect: QRect):
		# "paint" a square of ID: NONE to the storage to "unpaint" it
		self.paint(self.LABEL_IDS['NONE'], rect)

	def paint(self, layer_id, rect: QRect):
		if layer_id not in self.LABEL_IDS.values():
			print(f"{layer_id} not in LayerList")
		else:
			topleftX = rect.x()
			topleftY = rect.y()
			bottomrightX = topleftX + rect.width()
			bottomrightY = topleftY + rect.height()
			# print(f"Layer {layer_id}. TopLeft {topleftX},{topleftY} - BottomRight {bottomrightX},{bottomrightY}")
			self.label_map[topleftY:bottomrightY, topleftX:bottomrightX] = layer_id # Replacing data in storage matrix

	def clear(self):
		self.label_map: np.ndarray = np.zeros(self.dims, dtype=np.int8)
