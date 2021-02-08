from image import dicom_image
from PyQt5.QtWidgets import QProgressBar


class DicomSeries:
	def getImage(self, number: int): # starts at 1
		if number > len(self.images):
			raise ValueError("Selection too high in Series Image selection")
		return self.images[number - 1]

	def load_all(self, pb: QProgressBar = None):
		if pb is not None:
			pb.setMinimum(0)
			pb.setValue(0)
			pb.setMaximum(len(self.images))
		for i in self.images:
			i.load_content()
			if pb is not None:
				pb.setValue(pb.value() + 1)

	def __len__(self):
		return len(self.images)

	def __init__(self, path):
		self.path = path
		print('Series Init')
		self.images: [dicom_image] = None
