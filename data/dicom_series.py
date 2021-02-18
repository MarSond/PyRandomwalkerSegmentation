from image import dicom_image
from PyQt5.QtWidgets import QProgressBar


class DicomSeries:
	# Wraps an array of dicom_images for easier handling. Forwards loading function to each individual image

	def getImage(self, number: int):  # Image numbering starts at 1
		if number > len(self.images):
			raise ValueError("Requested image number is not present in series")
		return self.images[number - 1]

	def load_all(self, pb: QProgressBar = None):
		# Loop over all images and let them load the content themselves while updating ProgressBar
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

	def __init__(self, path: str):
		self.path: str = path
		self.images: [dicom_image] = None
