from PyQt5 import QtCore, QtGui, QtWidgets, uic
from data.data_manager import Datamanager
import image.segmentation as segment
from image.dicom_image import DicomImage
from data.image_label import ImageLabel
import numpy as np
from os.path import isdir
from timer import Timer
import gc


class UI_MainWindow(QtWidgets.QMainWindow):

	def update_preview_labeltext(self):
		sel_im = self.sl_raw_image.value()
		all_im = len(self.dataman.current_series)
		self.lb_preview.setText("Image {sel}/{all} selected. WC={wc} WW={ww}".format(
			sel=sel_im, all=all_im, ww=self.sl_ww.value(), wc=self.sl_wc.value()))

	def update_labelview(self):
		selected_image = self.sl_raw_image.value()
		cur_im: DicomImage = self.dataman.current_series.getImage(selected_image)
		label_map = cur_im.label.label_map
		self.lb_paint_bg.update_labelmap(label_map, [1])
		self.lb_raw_image.update_labelmap(label_map)

	def update_preview_window(self):
		self.lb_raw_image.update_window(wc=self.sb_wc.value(), ww=self.sb_ww.value())
		self.lb_raw_image.update()
		self.update_preview_labeltext()

	def update_preview_label(self):
		labels = self.curr_image.label.label_map
		self.lb_raw_image.update_labelmap(labels)
		self.lb_paint_all.update_labelmap(labels, [1, 2, 3])
		self.lb_paint_bg.update_labelmap(labels, [1])
		self.lb_paint_cl1.update_labelmap(labels, [2])
		self.lb_paint_cl2.update_labelmap(labels, [3])

	def update_preview(self):
		pixel = self.curr_image.pixels
		self.lb_raw_image.update_image(pixel)
		self.update_preview_window()
		self.update_preview_label()
		self.update()

	def sl_preview_alpha_changed(self):
		alpha_val = self.sl_preview_alpha.value() / 100
		self.lb_raw_image.update_transparency(alpha_val)
		self.lb_raw_image.update()

	def clb_load_click(self):
		path = self.le_path.text()
		if not isdir(path):
			self.le_path.setText("Please enter a valid path to an images containing folder")
			return None
		self.dataman.load_series(self.le_path.text(), self.pb_main)
		image_count = len(self.dataman.current_series)
		self.dataman.last_segresult = None
		self.dataman.last_segrange = None
		self.sl_raw_image.setMaximum(image_count)
		self.sl_res_image.setMaximum(image_count)
		self.gb_paint.setEnabled(True)
		self.gb_preview.setEnabled(True)
		self.gb_segmentation.setEnabled(False)
		self.gb_result.setEnabled(False)
		self.sb_raw.setEnabled(True)
		self.sb_wc.setEnabled(True)
		self.sb_ww.setEnabled(True)
		self.sl_paint_size.setEnabled(True)
		self.lb_preview.setEnabled(True)
		self.clb_start_segment.setEnabled(True)
		self.pb_clear_label.setEnabled(True)
		self.le_seg_range.setText("1-" + str(image_count))
		self.update_preview()

	def pb_select_folder_click(self):
		fname = QtWidgets.QFileDialog.getExistingDirectory(self, "Select image source folder")
		print("Selected folder:" + fname)
		self.le_path.setText(fname)

	def sl_res_image_changed(self):
		im_nr = self.sl_res_image.value()
		if self.dataman.last_segresult is not None and self.dataman.last_segrange[1] >= im_nr >= \
				self.dataman.last_segrange[0]:
			self.lb_result.update_image(self.dataman.current_series.getImage(im_nr).pixels)
			self.lb_result.update_labelmap(
				self.dataman.last_segresult[:, :, im_nr - self.dataman.last_segrange[0]], label_list=self.res_labelmode)
			print("Updated to Segmentation result " + str(im_nr))

	def __segment_single(self) -> np.ndarray:
		return segment.randomwalk_single(self.curr_image, window=self.hu_window, beta_val=self.beta_val,
		                                 data=self.dataman)

	def export_memtest(self, timelist, name="time_dict.csv"):
		print(timelist)
		self.dataman.paste_csv(timelist, name)

	def memtest_seg(self):
		run = 0
		timelist = dict()
		try:
			while run < len(self.dataman.current_series):
				print("***************************")
				run_add = 1  # Add to run count to speed up benchmarking
				if run >= 15:
					run_add = 2
				if run >= 25:
					run_add = 5
				if run > 50:
					run_add = 10
					self.export_memtest(timelist, name=f"run{run}_time_dict.csv")
				run += run_add
				gc.collect()
				t = Timer()
				t.start()
				segment.randomwalk_range(self.dataman.current_series, (1, run), window=self.hu_window,
				                         beta_val=self.beta_val, data=self.dataman)
				timelist[run] = t.stop()
				print(f"Run: {run}")
		except Exception as e:
			print(e)
			print(f"Exception at {run} images")
			self.export_memtest(timelist)
			return
		self.export_memtest(timelist)

	def __segment_range(self) -> np.ndarray:
		try:
			print("Segmentation range: " + str(self.seg_range))
			return segment.randomwalk_range(self.dataman.current_series, self.seg_range, window=self.hu_window,
			                                beta_val=self.beta_val, data=self.dataman)
		except Exception as e:
			print("EXCEPTION in __segment range")
			print(e)

	def clb_start_segment_click(self):
		try:
			if self.rb_seg_single.isChecked():
				pix_out_label = self.__segment_single()
				self.lb_result.update_image(self.dataman.current_series.getImage(self.sl_res_image.value()).pixels)
				self.lb_result.update_labelmap(pix_out_label)
			elif self.rb_seg_range.isChecked():
				timelist = list()
				for i in range(1):  # Change to set count of segmentations for time measurements
					t = Timer()
					t.start()
					pix_out_label = self.__segment_range()
				# pix_out_label = self.memtest_seg()
				timelist.append(t.stop())
				print(timelist)
				self.lb_result.update_image(self.dataman.current_series.getImage(self.sl_res_image.value()).pixels)
				self.lb_result.update_labelmap(pix_out_label[:, :, self.sl_res_image.value() - self.seg_range[0]])
			self.sl_res_image.setMaximum(self.seg_range[1])
			self.sl_res_image.setMinimum(self.seg_range[0])
			self.lb_result.update_window(wc=self.hu_window[0], ww=self.hu_window[1])
			self.dataman.last_segresult = np.atleast_3d(pix_out_label)
			self.dataman.last_segrange = self.seg_range
			self.gb_result.setEnabled(True)
			self.sb_res_image_selection.setEnabled(True)
			self.update_result_labelmode()
			self.update()
			print("Segmentation starting...")
		except Exception as e:
			print(e)

	def paint(self, e):
		self.gb_segmentation.setEnabled(True)
		self.sl_beta.setEnabled(True)
		if self.dataman.current_series is None:
			return None
		im_dim = self.curr_image.dims
		size_x = self.gv_raw_image.geometry().width()
		size_y = self.gv_raw_image.geometry().height()
		ratio_x = im_dim[1] / size_x
		ratio_y = im_dim[0] / size_y
		print("{} - {}".format(ratio_x, ratio_y))
		x_scaled = e.x() * ratio_x
		y_scaled = e.y() * ratio_y
		rect_label = QtCore.QRect(x_scaled, y_scaled, self.paint_size, self.paint_size)
		print("X: {} Y: {}".format(x_scaled, y_scaled))

		if self.preview_paint_left:
			self.curr_image.label.paint(self.current_paint_layer, rect_label)
		elif self.preview_paint_right:
			self.curr_image.label.unpaint(rect_label)
		self.update_preview_label()

	def mousePressEvent_preview(self, e: QtGui.QMouseEvent):
		if e.button() == QtCore.Qt.MouseButton.LeftButton:
			self.preview_paint_left = True
			self.preview_paint_right = False
		elif e.button() == QtCore.Qt.MouseButton.RightButton:
			self.preview_paint_left = False
			self.preview_paint_right = True
		self.paint(e)

	def mouseReleaseEvent_preview(self, e: QtGui.QMouseEvent):
		if e.button() == QtCore.Qt.MouseButton.LeftButton:
			self.preview_paint_left = True
			self.preview_paint_right = False
		elif e.button() == QtCore.Qt.MouseButton.RightButton:
			self.preview_paint_left = False
			self.preview_paint_right = True
		self.paint(e)

	def update_result_labelmode(self):
		if self.lb_result.array_label is not None:
			self.lb_result.update_transparency(self.sl_res_label_alpha.value() / 100)
			self.lb_result.update_labelmap(self.lb_result.array_label, self.res_labelmode)

	def pb_clear_label_click(self):
		self.curr_image.label.clear()
		self.update_preview()

	def pb_res_export_click(self):
		print(self.seg_range)
		export_path = self.dataman.create_export_folder(self.dataman.current_series.path)
		print("Exporting to {}".format(export_path))
		self.pb_main.setMinimum(self.seg_range[0])
		self.pb_main.setMaximum(self.seg_range[1])
		index: int = 0
		self.dataman.export_pixmap(self.lb_raw_image.pixmap_full, name="SEEDS-WW{ww}-WC{wc}-B{beta}".format(
			ww=self.hu_window[1], wc=self.hu_window[0], beta=self.beta_val), base_path=export_path)
		for i in range(self.seg_range[0], self.seg_range[1] + 1):
			self.pb_main.setValue(i)
			self.lb_result.update_image(self.dataman.current_series.getImage(i).pixels)
			label_mat = self.dataman.last_segresult[:, :, index]
			self.lb_result.update_labelmap(label_mat, label_list=self.res_labelmode)
			self.dataman.export_pixmap(self.lb_result.pixmap_full, name="{im}-WW{ww}-WC{wc}-B{beta}".format(
				im=i, ww=self.hu_window[1], wc=self.hu_window[0], beta=self.beta_val), base_path=export_path)
			index += 1

	def __init__(self):
		super(UI_MainWindow, self).__init__()
		self.dataman: Datamanager = Datamanager()
		self.preview_paint_left = False
		self.preview_paint_right = False
		self.__seg_range = (0, 0)
		self.__current_paint_layer = ImageLabel.LABEL_IDS['NONE']
		self.__current_paint_color = ImageLabel.color_bg
		self.__beta_val = 0
		self.__hu_window = (100, 200)
		self.__res_labelmode = [1, 2, 3]
		uic.loadUi('GUI/Main.ui', self)
		self.sl_raw_image = self.findChild(QtWidgets.QSlider, 'sl_raw_image')
		self.sl_raw_image.valueChanged.connect(self.update_preview)
		###################
		self.clb_load = self.findChild(QtWidgets.QCommandLinkButton, 'clb_load')
		self.clb_load.clicked.connect(self.clb_load_click)
		self.clb_start_segment = self.findChild(QtWidgets.QCommandLinkButton, 'clb_start_segment')
		self.clb_start_segment.clicked.connect(self.clb_start_segment_click)
		###################
		self.pb_select_folder = self.findChild(QtWidgets.QPushButton, 'pb_select_folder')
		self.pb_select_folder.clicked.connect(self.pb_select_folder_click)
		###################
		self.sl_beta = self.findChild(QtWidgets.QSlider, 'sl_beta')
		self.sb_beta = self.findChild(QtWidgets.QSpinBox, 'sb_beta')
		self.sl_ww = self.findChild(QtWidgets.QSlider, 'sl_ww')
		self.sl_ww.valueChanged.connect(self.update_preview_window)
		self.sb_ww = self.findChild(QtWidgets.QSpinBox, 'sb_ww')
		###################
		self.sl_wc = self.findChild(QtWidgets.QSlider, 'sl_wc')
		self.sl_wc.valueChanged.connect(self.update_preview_window)
		self.sb_wc = self.findChild(QtWidgets.QSpinBox, 'sb_wc')
		self.sb_raw = self.findChild(QtWidgets.QSpinBox, 'sb_raw')
		###################
		self.le_path = self.findChild(QtWidgets.QLineEdit, 'le_path')
		self.pb_main = self.findChild(QtWidgets.QProgressBar, 'pb_main')
		self.lb_raw_image = self.findChild(QtWidgets.QLabel, 'gv_raw_image')
		self.lb_result = self.findChild(QtWidgets.QLabel, 'lb_result')
		self.lb_raw_image.mousePressEvent = lambda event: self.mousePressEvent_preview(event)
		self.lb_raw_image.mouseReleaseEvent = lambda event: self.mouseReleaseEvent_preview(event)
		self.lb_raw_image.mouseMoveEvent = lambda event: self.paint(event)
		self.lb_preview = self.findChild(QtWidgets.QLabel, 'lb_preview')
		################### Image Labels
		self.lb_paint_bg = self.findChild(QtWidgets.QLabel, 'lb_paint_bg')
		self.lb_paint_cl1 = self.findChild(QtWidgets.QLabel, 'lb_paint_cl1')
		self.lb_paint_cl2 = self.findChild(QtWidgets.QLabel, 'lb_paint_cl2')
		self.lb_paint_all = self.findChild(QtWidgets.QLabel, 'lb_paint_all')
		###################
		self.gb_paint = self.findChild(QtWidgets.QGroupBox, 'gb_paint_settings')
		self.gb_preview = self.findChild(QtWidgets.QGroupBox, 'gb_preview_settings')
		self.gb_result = self.findChild(QtWidgets.QGroupBox, 'gb_result_settings')
		self.gb_segmentation = self.findChild(QtWidgets.QGroupBox, 'gb_segmentation_settings')
		###################
		self.cb_res_lb1 = self.gb_result.findChild(QtWidgets.QCheckBox, 'cb_res_label_1')
		self.cb_res_lb1.stateChanged.connect(self.update_result_labelmode)
		self.cb_res_lb2 = self.gb_result.findChild(QtWidgets.QCheckBox, 'cb_res_label_2')
		self.cb_res_lb2.stateChanged.connect(self.update_result_labelmode)
		self.cb_res_bg = self.gb_result.findChild(QtWidgets.QCheckBox, 'cb_res_label_bg')
		self.cb_res_bg.stateChanged.connect(self.update_result_labelmode)
		self.sl_res_label_alpha = self.gb_result.findChild(QtWidgets.QSlider, 'sl_res_label_alpha')
		self.sl_res_label_alpha.valueChanged.connect(self.update_result_labelmode)
		self.sl_res_image = self.gb_result.findChild(QtWidgets.QSlider, 'sl_res_image')
		self.sl_res_image.valueChanged.connect(self.sl_res_image_changed)
		self.pb_res_export = self.gb_result.findChild(QtWidgets.QPushButton, 'pb_res_export')
		self.pb_res_export.clicked.connect(self.pb_res_export_click)
		###################
		self.rb_seg_single = self.gb_segmentation.findChild(QtWidgets.QRadioButton, 'rb_seg_single')
		self.rb_seg_range = self.gb_segmentation.findChild(QtWidgets.QRadioButton, 'rb_seg_range')
		self.le_seg_range = self.gb_segmentation.findChild(QtWidgets.QLineEdit, 'le_seg_range')
		###################
		self.rb_paint_bg = self.gb_paint.findChild(QtWidgets.QRadioButton, 'rb_paint_bg')
		self.rb_paint_cl1 = self.gb_paint.findChild(QtWidgets.QRadioButton, 'rb_paint_cl1')
		self.rb_paint_cl2 = self.gb_paint.findChild(QtWidgets.QRadioButton, 'rb_paint_cl2')
		self.sb_paint_size = self.findChild(QtWidgets.QSpinBox, 'sb_paint_size')
		self.sl_paint_size = self.gb_paint.findChild(QtWidgets.QSlider, 'sl_paint_size')
		self.pb_clear_label = self.gb_paint.findChild(QtWidgets.QPushButton, 'pb_clear_label')
		self.pb_clear_label.clicked.connect(self.pb_clear_label_click)
		self.sl_preview_alpha = self.gb_paint.findChild(QtWidgets.QSlider, 'sl_preview_alpha')
		self.sl_preview_alpha.valueChanged.connect(self.sl_preview_alpha_changed)
		self.show()
		######################
		self.__paint_size = self.sb_paint_size.value()

	# OPTIONAL Datamanager für Debug Export
	# self.lb_raw_image.setDataman(self.data, "lb_raw_im")
	# self.lb_result.setDataman(self.data, "lb_result")
	# self.lb_paint_all.setDataman(self.data, "label all")
	# self.lb_paint_bg.setDataman(self.data, "label bg")
	# self.lb_paint_cl1.setDataman(self.data, "label 1")
	# self.lb_paint_cl2.setDataman(self.data, "label 2")

	@property
	def seg_range(self):
		return self.__seg_range

	@seg_range.getter
	def seg_range(self):
		if self.rb_seg_single.isChecked():
			return self.sl_res_image.value(), self.sl_res_image.value()
		else:
			return tuple(map(int, self.le_seg_range.text().split('-')))

	@property
	def res_labelmode(self):
		return self.__res_labelmode

	@res_labelmode.getter
	def res_labelmode(self):
		layer = []
		if self.cb_res_bg.isChecked():
			layer.append(1)
		if self.cb_res_lb1.isChecked():
			layer.append(2)
		if self.cb_res_lb2.isChecked():
			layer.append(3)
		return layer

	@property
	def hu_window(self):
		return self.__hu_window

	@hu_window.getter
	def hu_window(self):
		# Houndsfield Unit -- 0: Center  1: Width
		return self.sl_wc.value(), self.sl_ww.value()

	@property
	def beta_val(self):
		return self.__beta_val

	@beta_val.getter
	def beta_val(self):
		return self.sb_beta.value()

	@property
	def curr_image(self):
		return self.dataman.getImage(self.sl_raw_image.value())

	@property
	def paint_size(self):
		return self.__paint_size

	@paint_size.getter
	def paint_size(self):
		return self.sb_paint_size.value()

	@property
	def current_paint_layer(self):
		return self.__current_paint_layer

	@current_paint_layer.getter
	def current_paint_layer(self):
		if self.rb_paint_bg.isChecked():
			return ImageLabel.LABEL_IDS['BG']
		elif self.rb_paint_cl1.isChecked():
			return ImageLabel.LABEL_IDS['CL1']
		elif self.rb_paint_cl2.isChecked():
			return ImageLabel.LABEL_IDS['CL2']
		else:
			raise ValueError("No known paint checkbox for Layer")

	@property
	def current_paint_color(self):
		return self.__current_paint_layer

	@current_paint_color.getter
	def current_paint_color(self):
		if self.rb_paint_bg.isChecked():
			return self.color_bg
		elif self.rb_paint_cl1.isChecked():
			return self.color_cl1
		elif self.rb_paint_cl2.isChecked():
			return self.color_cl2
		else:
			raise ValueError("No known paint checkbox for color")
