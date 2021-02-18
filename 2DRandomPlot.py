import numpy
import pylab
import random

n = 100000
x = numpy.zeros(n)
y = numpy.zeros(n)

for i in range(1, n):
	ran = random.randint(1, 4)
	if ran == 1:  # rechts
		x[i] = x[i - 1] + 1
		y[i] = y[i - 1]
	elif ran == 2:
		x[i] = x[i - 1] - 1
		y[i] = y[i - 1]
	elif ran == 3:
		x[i] = x[i - 1]
		y[i] = y[i - 1] + 1
	else:
		x[i] = x[i - 1]
		y[i] = y[i - 1] - 1
pylab.title("2D Random Walker")
pylab.plot(x, y)
pylab.show()
