import numpy as np
import pydicom as dcm
import os.path
from data.image_label import ImageLabel
from PIL import Image


class DicomImage:
	# Stores image pixel data and its own label map. Loads itself from either DICOM or .png/.jpg

	def load_content(self):
		try:
			if '.png' in self.file_name or '.jpg' in self.file_name:
				self.dicom_format = False
				image: Image = Image.open(self.path).convert('L')  # Load image and convert to greyscale
				self.pixels = np.asarray(image)
			else:
				self.dicom_format = True
				file_data = dcm.dcmread(self.path)
				try:
					rescaleIntercept = file_data[0x0028, 0x1052].value
					rescaleSlope = file_data[0x0028, 0x1053].value
				except Exception:
					# In case exception is thrown, the values are not present. Likely non CT-image -> use standard
					rescaleIntercept = 0
					rescaleSlope = 1
				raw = file_data.pixel_array
				self.pixels = raw * rescaleSlope + rescaleIntercept
				self.file_data = file_data
			# print(f"File datatye {str(self.pixels.dtype)}")
			self.pixels = self.pixels.astype(np.int16)
			self.loaded = True
			self.label = ImageLabel(self.dims)
		except FileNotFoundError:
			print(f"File {self.path} does not exist")
			self.loaded = False
		except Exception as e:
			print(e)
			print(f"Error loading image {self.path}")
			self.loaded = False

	@property
	def dims(self):
		return self.__dims

	@dims.getter
	def dims(self):
		if not self.loaded or self.pixels is None:
			raise Exception("Image is not loaded - No dimensions avaible")
		return np.shape(self.pixels)

	def __init__(self, path, dicom_format=True):
		head, tail = os.path.split(path)
		self.__dims = None
		self.path: str = path
		self.dicom_format = dicom_format
		self.file_name: str = tail
		self.label: ImageLabel = None
		self.file_data: dcm.dataset.FileDataset = None
		self.pixels: np.ndarray = None
		self.loaded = False
		self.dicom_format = True
