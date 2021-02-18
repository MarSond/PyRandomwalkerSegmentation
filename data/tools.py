import numpy as np
import time


def window_hu(raw, wc, ww):
	# Houndsfield window function
	_min = 0
	_max = 255  # Normal monitor pixel intensity range
	if raw <= (wc - 0.5 - (ww - 1) / 2):
		target = _min
	elif raw > (wc - 0.5 + (ww - 1) / 2):
		target = _max
	else:
		target = ((raw - (wc - 0.5)) / (ww - 1) + 0.5) * ((_max - _min) + _min)
	return target


def arr_hu_to_arr(array: np.ndarray, ww: int, wc: int) -> np.ndarray:
	# Use numpy.vectorize to apply window function on each cell
	hu_func = lambda h: window_hu(h, ww=ww, wc=wc)
	vect_hu = np.vectorize(hu_func)
	return vect_hu(array)


class Timer:
	def __init__(self):
		self._start_time = None

	def start(self):
		"""Start a new timer"""
		if self._start_time is not None:
			raise Exception(f"Timer is running. Use .stop() to stop it")

		self._start_time = time.perf_counter()

	def stop(self):
		"""Stop the timer, and report the elapsed time"""
		if self._start_time is None:
			raise Exception(f"Timer is not running. Use .start() to start it")

		elapsed_time = time.perf_counter() - self._start_time
		self._start_time = None
		print(f"Elapsed time: {elapsed_time:0.4f} seconds")
		return elapsed_time
