from PyQt5.QtCore import QFile, QIODevice
from PyQt5.QtGui import QPixmap
from image.dicom_series import DicomSeries
from image.dicom_image import DicomImage
from PyQt5.QtWidgets import QProgressBar
import os, time, random, re, csv, threading, pathlib
import numpy as np
from matplotlib import pyplot as plt
from typing import Tuple


class ExportWriter(object):
	def __init__(self, data, path):
		self.data = data
		self.path = path
		thread = threading.Thread(target=self.run, args=())
		thread.start()

	def run(self):
		try:
			if type(self.data) is not list:
				all_obj = [self.data]
			for i in all_obj:
				if type(i) == QPixmap:
					f: QFile = QFile(self.path)
					f.open(QIODevice.WriteOnly)
					i.save(f, "PNG")
				elif type(self.data) == np.ndarray:
					plt.imsave(self.path, i)
		except ValueError as ve:
			return  # Expected sometimes
		except Exception as e:
			print(e)

def getDateString():
	return time.strftime("%d.%m %H-%M-%S", time.localtime())


class Datamanager:

	def __init__(self):
		self.current_series: DicomSeries = None
		self.base_dir = os.getcwd()
		self.current_export_path: str = None
		self.export_names: dict = {}
		self.last_segresult: np.ndarray = None
		self.last_segrange: tuple = None

	def getPixelLabel3D(self, series: DicomSeries = None, im_range: tuple = (1, None)) -> Tuple[np.ndarray, np.ndarray]:
		if series is None:
			series = self.current_series
		if im_range[1] is None:
			im_range = im_range(im_range[0], len(series))
		first_im: DicomImage = series.getImage(im_range[0])
		dims = first_im.dims
		vol: np.ndarray = first_im.pixels
		label: np.ndarray = first_im.label.label_map
		for i in range(im_range[0] + 1, im_range[1] + 1):
			image: DicomImage = series.getImage(i)
			c_pixel: np.ndarray = image.pixels
			c_label: np.ndarray = image.label.label_map
			vol = np.dstack((vol, c_pixel))
			label = np.dstack((label, c_label))
		return vol, label

	def getImage(self, number):
		if number > len(self.current_series):
			raise ValueError('Requested Image Number not loaded')
		return self.current_series.getImage(number)

	def create_export_folder(self, image_path) -> str:
		parent = os.path.abspath(os.path.join(image_path, os.pardir))
		series_name = os.path.basename(image_path)
		new_name = series_name + "-" + getDateString()
		try:
			export_dir = os.path.join(parent, new_name)
			if not os.path.isdir(export_dir):
				os.mkdir(export_dir)
			return export_dir
		except Exception as e:
			print(e)
			print("Error creating Export Folder")
			return None

	def create_series_folder(self):
		try:
			export_dir = os.path.join(self.base_dir, "\\export")
			if not os.path.isdir(export_dir):
				os.mkdir(export_dir)
			dirstring = os.path.join(export_dir, getDateString())
			print(dirstring)
			os.mkdir(dirstring)
			self.current_export_path = dirstring
		except Exception as e:
			print(e)
			print("Error creating debug export Folder")
			self.current_export_path = None

	def paste_csv(self, input: dict, path="default.txt"):
		try:
			finalpath=pathlib.Path(__file__).parent.parent.absolute().joinpath("measurements\\").joinpath(path)
			with open(finalpath, 'w') as f:
				for key in input.keys():
					f.write("%s;%s\n" % (key, input[key]))
		except IOError:
			print("I/O error")

	def __get_export_fname(self, name, folder=None):
		if folder is None and self.current_export_path is None:
			raise Exception("Path Null")
		elif folder is None:
			folder = self.current_export_path
		if name is None:
			f_name = str(random.randint(1000, 9999))
		else:
			if name in self.export_names:
				f_name = name + "-" + str(self.export_names[name])
				self.export_names[name] = self.export_names[name] + 1
			else:
				self.export_names[name] = 1
				f_name = name + "-1"
		path = os.path.join(folder, f_name + ".png")
		print("Export to " + path)
		return path

	def export_np(self, arr: np.ndarray, name: str = None, base_path=None):
		path = self.__get_export_fname(name, base_path)
		ExportWriter(arr, path)

	def export_pixmap(self, pix: QPixmap, name: str = None, base_path=None):
		try:
			path = self.__get_export_fname(name, base_path)
			ExportWriter(pix, path)
		except Exception as e:
			print(e)
			print("Error saving Pixmap")

	def load_series(self, path, pb: QProgressBar = None):
		new_s = DicomSeries(path)
		print('Path to the DICOM directory: {}'.format(path))
		image_list: DicomImage = []
		for r, d, f in os.walk(path):
			try:
				f.sort(key = lambda x: int(re.sub(r"\D", "", x)))
			except Exception:
				print("Sort omitted")
			for file in f:
				temp_path = os.path.join(path, file)
				temp_image = DicomImage(temp_path)
				image_list.append(temp_image)
			break
		new_s.images = image_list
		print("{} images found. Start loading".format(len(image_list)))
		new_s.load_all(pb)
		print("Everything loaded")
		self.create_series_folder()
		self.current_series = new_s
