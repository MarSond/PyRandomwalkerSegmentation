from PyQt5.QtGui import QPixmap, QPainter, QImage
import numpy as np


def window_hu(raw, wc, ww):
	_min = 0
	_max = 255 # Normal monitor pixel intensity range
	if raw <= (wc - 0.5 - (ww - 1) / 2):
		target = _min
	elif raw > (wc - 0.5 + (ww - 1) / 2):
		target = _max
	else:
		target = ((raw - (wc - 0.5)) / (ww - 1) + 0.5) * ((_max - _min) + _min)
	return target


def win_scale(data, wl, ww, dtype=np.float, out_range=(0, 255)):
	# Scale pixel intensity data using specified window level, width, and intensity range.
	data_new = np.empty(data.shape, dtype=np.float)
	data_new.fill(out_range[1] - 1)

	data_new[data <= (wl - ww / 2.0)] = out_range[0]
	data_new[(data > (wl - ww / 2.0)) & (data <= (wl + ww / 2.0))] = \
		((data[(data > (wl - ww / 2.0)) & (data <= (wl + ww / 2.0))] - (wl - 0.5)) / (ww - 1.0) + 0.5) * (
				out_range[1] - out_range[0]) + out_range[0]
	data_new[data > (wl + ww / 2.0)] = out_range[1] - 1

	return data_new.astype(dtype)


def arr_hu_to_arr(array: np.ndarray, ww: int, wc: int) -> np.ndarray:
	hu_func = lambda h: window_hu(h, ww=ww, wc=wc)
	vect_hu = np.vectorize(hu_func)
	return vect_hu(array)


def paint_ontop(target: QPixmap, overlay: QPixmap):
	oImage = QImage(overlay.size(), QImage.Format_ARGB32)
	oP = QPainter(oImage)
	oP.drawImage(0, 0, overlay)
	oP.end()
	painter = QPainter(target)
	painter.drawImage(0, 0, oImage)
	painter.end()
	return target
