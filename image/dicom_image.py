import numpy as np
import pydicom as dcm
import os.path
from data.image_label import ImageLabel
from PIL import Image


class DicomImage:

	def load_content(self):
		try:
			if '.png' in self.f_name or '.jpg' in self.f_name:
				self.dicom_format = False
				image: Image = Image.open(self.path).convert('L')
				self.pixels = np.asarray(image)
			else:
				f_data = dcm.dcmread(self.path)
				try:
					rescaleIntercept = f_data[0x0028, 0x1052].value
					rescaleSlope = f_data[0x0028, 0x1053].value
				except:
					rescaleIntercept = 0
					rescaleSlope = 1
				raw = f_data.pixel_array
				self.pixels = raw * rescaleSlope + rescaleIntercept
				self.f_data = f_data
			print("File Datatye "+str(self.pixels.dtype))
			self.pixels = self.pixels.astype(np.int16)
			self.loaded = True
			self.label = ImageLabel(self.dims)
		except FileNotFoundError:
			print("File "+self.path+" does not exist")
			self.loaded = False
		except Exception as e:
			print(e)
			print("Error loading image {}".format(self.path))
			self.loaded = False

	@property
	def dims(self):
		return self.__dims

	@dims.getter
	def dims(self):
		if not self.loaded or self.pixels is None:
			raise Exception("Image not loaded")
		return np.shape(self.pixels)

	def __init__(self, path, dicom_format=True):
		head, tail = os.path.split(path)
		self.__dims = None
		self.path: str = path
		self.dicom_format = dicom_format
		self.f_name: str = tail
		self.label: ImageLabel = None
		self.f_data: dcm.dataset.FileDataset = None
		self.pixels: np.ndarray = None
		self.loaded = False
		self.dicom_format = True
