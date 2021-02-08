"""
Random walker segmentation algorithm

from *Random walks for image segmentation*, Leo Grady, IEEE Trans
Pattern Anal Mach Intell. 2006 Nov;28(11):1768-83.

**************

Copyright (C) 2011, the scikit-image team All rights reserved.

Modified by Martin Sondermann using the base version from the scikit-image library
"""
import numpy as np
from scipy import sparse, ndimage as ndi
from pyamg import ruge_stuben_solver
from skimage import img_as_float
from scipy.sparse.linalg import cg


def _make_graph_edges_3d(n_x, n_y, n_z):
	vertices = np.arange(n_x * n_y * n_z).reshape((n_x, n_y, n_z))
	edges_deep = np.vstack((vertices[..., :-1].ravel(), vertices[..., 1:].ravel()))
	edges_right = np.vstack((vertices[:, :-1].ravel(), vertices[:, 1:].ravel()))
	edges_down = np.vstack((vertices[:-1].ravel(), vertices[1:].ravel()))
	edges = np.hstack((edges_deep, edges_right, edges_down))
	return edges


def _compute_weights_3d(data, spacing, beta, eps):
	gradients = np.concatenate(
		[np.diff(data[..., 0], axis=ax).ravel() / spacing[ax] for ax in [2, 1, 0] if data.shape[ax] > 1], axis=0) ** 2
	for channel in range(1, data.shape[-1]):
		gradients += np.concatenate([np.diff(data[..., channel], axis=ax).ravel() / spacing[ax] for ax in [2, 1, 0] if data.shape[ax] > 1], axis=0) ** 2
	scale_factor = -beta / (10 * data.std())
	weights = np.exp(scale_factor * gradients)
	weights += eps
	#weights=weights.astype(np.float32) # Coversion did cause NaN's
	return -weights


def _build_laplacian(data, spacing, mask, beta):
	l_x, l_y, l_z = data.shape[:3]
	edges = _make_graph_edges_3d(l_x, l_y, l_z)
	weights = _compute_weights_3d(data, spacing, beta=beta, eps=1.e-8)
	# Build the sparse linear system
	pixel_nb = edges.shape[1]
	i_indices = edges.ravel()
	j_indices = edges[::-1].ravel()
	data = np.hstack((weights, weights))
	lap = sparse.coo_matrix((data, (i_indices, j_indices)), shape=(pixel_nb, pixel_nb))
	del data
	lap.setdiag(-np.ravel(lap.sum(axis=0)))
	return lap.tocsr()


def _build_linear_system(data, spacing, labels, nlabels, mask, beta):
	"""
	Build the matrix A and rhs B of the linear system to solve.
	A and B are two block of the laplacian of the image graph.
	"""
	if mask is None:
		labels = labels.ravel()
	else:
		labels = labels[mask]
	indices = np.arange(labels.size)
	seeds_mask = labels > 0
	unlabeled_indices = indices[~seeds_mask]
	seeds_indices = indices[seeds_mask]
	lap_sparse = _build_laplacian(data, spacing, mask=mask, beta=beta)
	rows = lap_sparse[unlabeled_indices, :]
	lap_sparse = rows[:, unlabeled_indices]
	B = -rows[:, seeds_indices]
	seeds = labels[seeds_mask]
	seeds_mask = sparse.csc_matrix(np.hstack([np.atleast_2d(seeds == lab).T for lab in range(1, nlabels + 1)]))
	rhs = B.dot(seeds_mask)
	return lap_sparse, rhs


def _solve_linear_system(lap_sparse, B, tol):
	lap_sparse = lap_sparse.tocsr()
	ml = ruge_stuben_solver(lap_sparse)
	M = ml.aspreconditioner(cycle='V')
	cg_out = [cg(lap_sparse, B[:, i].toarray(), tol=tol, M=M, maxiter=30) for i in range(B.shape[1])]
	X = np.asarray([x for x, _ in cg_out])
	return X


def _preprocess(labels):
	label_values, inv_idx = np.unique(labels, return_inverse=True)
	# If some labeled pixels are isolated inside pruned zones, prune them
	# as well and keep the labels for the final output
	null_mask = labels == 0
	pos_mask = labels > 0
	mask = labels >= 0
	fill = ndi.binary_propagation(null_mask, mask=mask)
	isolated = np.logical_and(pos_mask, np.logical_not(fill))
	pos_mask[isolated] = False
	# If the array has pruned zones, be sure that no isolated pixels
	# exist between pruned zones (they could not be determined)
	if label_values[0] < 0 or np.any(isolated):
		isolated = np.logical_and(
			np.logical_not(ndi.binary_propagation(pos_mask, mask=mask)), null_mask)
		labels[isolated] = -1
		if np.all(isolated[null_mask]):
			return labels, None, None, None, None
		mask[isolated] = False
		mask = np.atleast_3d(mask)
	else:
		mask = None
	# Reorder label values to have consecutive integers (no gaps)
	zero_idx = np.searchsorted(label_values, 0)
	labels = np.atleast_3d(inv_idx.reshape(labels.shape) - zero_idx)
	nlabels = label_values[zero_idx + 1:].shape[0]
	inds_isolated_seeds = np.nonzero(isolated)
	isolated_values = labels[inds_isolated_seeds]
	return labels, nlabels, mask, inds_isolated_seeds, isolated_values


def random_walker(data, labels, beta=130, tol=1.e-3, copy=False):
	spacing = np.ones(3)
	if data.ndim not in (2, 3):
		raise ValueError('For non-multichannel input, data must be of dimension 2 or 3.')
	if data.shape != labels.shape:
		raise ValueError('Incompatible data and labels shapes.')
	data = np.atleast_3d(img_as_float(data))[..., np.newaxis]
	labels_shape = labels.shape
	labels_dtype = labels.dtype
	if copy:
		labels = np.copy(labels)
	(labels, nlabels, mask, inds_isolated_seeds, isolated_values) = _preprocess(labels)
	# Build the linear system (lap_sparse, B)
	lap_sparse, B = _build_linear_system(data, spacing, labels, nlabels, mask, beta)

	# Solve the linear system lap_sparse X = B
	# where X[i, j] is the probability that a marker of label i arrives
	# first at pixel j by anisotropic diffusion.
	X = _solve_linear_system(lap_sparse, B, tol)
	# Build the output according to return_full_prob value
	# Put back labels of isolated seeds
	labels[inds_isolated_seeds] = isolated_values
	labels = labels.reshape(labels_shape)

	X = np.argmax(X, axis=0) + 1
	out = labels.astype(labels_dtype)
	out[labels == 0] = X
	return out
