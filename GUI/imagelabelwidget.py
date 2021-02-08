from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QColor, QPainter
from PyQt5.QtCore import Qt, QSize
import image.image_functions as imf
import numpy as np
import qimage2ndarray
from data.data_manager import Datamanager
from data.image_label import ImageLabel


class ImageLabelWidget(QtWidgets.QLabel):

	def scale_pixmap(self, pixmap: QPixmap) -> QPixmap:
		target_geom = self.frameGeometry()
		return pixmap.scaled(QSize(target_geom.width(), target_geom.height()))

	def labelmap_to_pixmap(self, label_array: np.ndarray, background_pix: QPixmap = None,
	                       label_list=[1, 2, 3]) -> QPixmap:
		if background_pix is None:
			background = QPixmap(label_array.shape[0], label_array.shape[1])
			background.fill(Qt.transparent)
		else:
			background = background_pix.copy()
		if self.dataman is not None:
			self.dataman.export_pixmap(background, "background-" + self.name)
		t_painter = QPainter(background)
		pix_label = QPixmap.fromImage(qimage2ndarray.gray2qimage(label_array))
		mask_none = pix_label.createMaskFromColor(QColor(0, 0, 0), Qt.MaskOutColor)
		for id in label_list:
			mask = pix_label.createMaskFromColor(QColor(id, id, id), Qt.MaskOutColor)
			t_painter.setPen(ImageLabel.LABEL_COLORS.get(str(id)))
			t_painter.drawPixmap(background.rect(), mask, mask.rect())
		t_painter.end()
		return background

	def update_image(self, array: np.ndarray):
		self.array_data = array
		self.update_full()

	def update_full(self):
		self.update_window(ww=self.last_ww, wc=self.last_wc, force=True)
		self.apply_pixmap()

	def apply_pixmap(self, pix=None):
		if pix is None:
			if self.pixmap_full is None:
				raise Exception("No pixmap avaible")
			self.setPixmap(self.pixmap_full)
		else:
			self.setPixmap(pix)
		self.update()

	def fuse_pixmap(self, pix_data: QPixmap = None, pix_label: QPixmap = None, alpha: float = 1.0) -> QPixmap:
		if pix_data is None:
			pix_data = self.pixmap_data
		if pix_label is None:
			pix_label = self.pixmap_label
		if pix_data is None and pix_label is None:
			raise Exception("No data to fuse")
		if pix_data is None and type(pix_label) == QPixmap:
			pix_data = QPixmap(pix_label.width(), pix_label.height())
			pix_data.fill(QColor(255, 255, 255))
		if pix_label is None:
			print("Label none")
			return pix_data
		target: QPixmap = pix_data.copy()
		label = pix_label.copy()
		mask_none = pix_label.createMaskFromColor(QColor(0, 0, 0), Qt.MaskInColor)
		label.setMask(mask_none)
		paint = QPainter(target)
		paint.setOpacity(alpha)
		paint.drawPixmap(0, 0, label)
		paint.end()
		return target

	def update_labelmap(self, labels: np.ndarray, label_list=[1, 2, 3]):
		self.array_label = labels
		pixmap_label_raw = self.labelmap_to_pixmap(label_array=self.array_label, label_list=label_list)
		self.pixmap_label = self.scale_pixmap(pixmap=pixmap_label_raw)
		self.pixmap_full = self.fuse_pixmap(None, self.pixmap_label, alpha=self.alpha)
		self.apply_pixmap(self.pixmap_full)
		if self.dataman is not None:
			self.dataman.export_np(labels, "numpy-label {} {}".format(str(label_list), self.name))
			self.dataman.export_pixmap(pixmap_label_raw, "label to pix raw {} {}".format(str(label_list), self.name))
			self.dataman.export_pixmap(self.pixmap_full, "pix-full {} {}".format(str(label_list), self.name))
			self.dataman.export_pixmap(self.pixmap_label, "pix-label {} {}".format(str(label_list), self.name))

	def set_pixmap_data(self, pix_data: QPixmap):
		self.pixmap_data = self.scale_pixmap(pixmap=pix_data)
		self.pixmap_full = self.fuse_pixmap(None, None, self.alpha)
		self.apply_pixmap()

	def update_pixmap(self, array: np.ndarray):
		pixmap_raw = QPixmap.fromImage(qimage2ndarray.gray2qimage(array))
		self.pixmap_data = self.scale_pixmap(pixmap=pixmap_raw)
		self.pixmap_full = self.fuse_pixmap(self.pixmap_data, self.pixmap_label, alpha=self.alpha)
		self.apply_pixmap(self.pixmap_full)

	def update_window(self, ww, wc, force=False):
		if ww != self.last_ww or wc != self.last_wc or force is True:
			hu_array = imf.arr_hu_to_arr(self.array_data, ww=ww, wc=wc)
			self.update_pixmap(hu_array)
			self.last_ww = ww
			self.last_wc = wc
			print("HU updated on label")

	def update_transparency(self, alpha_val):
		self.alpha = alpha_val
		self.pixmap_full = self.fuse_pixmap(None, None, alpha_val)
		self.apply_pixmap()

	def setDataman(self, dataman, name="default"):
		self.dataman = dataman
		self.name = name

	def __init__(self, *args, **kwargs):
		super(ImageLabelWidget, self).__init__(*args, **kwargs)
		self.setText("Test")
		self.update()
		self.alpha: float = 1.0
		self.last_ww = 0
		self.last_wc = 0
		self.array_data = None
		self.array_label = None
		self.pixmap_data: QPixmap = None
		self.pixmap_label: QPixmap = None
		self.pixmap_full: QPixmap = None
		self.dataman: Datamanager = None
		self.name = "default"
		print("label init")
