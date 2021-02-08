from image.dicom_image import DicomImage
from image.dicom_series import DicomSeries
import image.randomwalker_self as ran_self
import numpy as np
import image.image_functions as imp
from data.data_manager import Datamanager
from typing import Tuple


def __get_data3D(series: DicomSeries, seg_range: tuple, window: tuple, data: Datamanager) -> Tuple[np.ndarray, np.ndarray]:
	volume, label = data.getPixelLabel3D(series=series, im_range=seg_range)  # get both matrices of data and label
	data = imp.arr_hu_to_arr(volume, wc=window[0], ww=window[1])             # HU transform of data
	data_normalized = (data - np.min(data)) / np.ptp(data)
	return data_normalized, label


def randomwalk_range(series: DicomSeries, seg_range: tuple, window: tuple, beta_val: float, data: Datamanager) -> np.ndarray:
	vol_data, vol_label = __get_data3D(series=series, seg_range=seg_range, window=window, data=data)
	print("Start segmentation self with wc={} ww={} beta={}".format(window[0], window[1], beta_val))
	seg = ran_self.random_walker(vol_data, vol_label, copy=False, beta=beta_val)
	#data.export_np(seg, "seg-range") if data is not None else None
	return np.atleast_3d(seg)  # export matrix anyways as 3D to not confuse later on


def randomwalk_single(image: DicomImage, window: tuple, beta_val: float, data: Datamanager = None) -> np.ndarray:
	im_data = imp.arr_hu_to_arr(image.pixels, wc=window[0], ww=window[1])
	data_normalized = (im_data - np.min(im_data)) / np.ptp(im_data)
	print("Start segmentation scikit with wc={} ww={} beta={}".format(window[0], window[1], beta_val))
	seg = ran_self.random_walker(data_normalized, image.label.label_map, copy=False, beta=beta_val)
	data.export_np(seg, "seg-single") if data is not None else None
	return seg
