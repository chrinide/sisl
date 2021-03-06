from __future__ import print_function, division

import numpy as np

import sisl._array as _a
from sisl._help import _zip as zip, _range as range


__all__ = ['EigenSystem']

_conj = np.conjugate
_outer_ = np.outer


def _outer(e, v):
    return _outer_(v * e, _conj(v))


class EigenSystem(object):
    """ A class for retaining eigenvalues and eigenvectors

    Although an *eigensystem* is generally referred to as *all* eigenvalues
    and eigenvectors for a given linear transformation it is noticable
    that this class does not necessarily contain all such quantities, it
    may be a subset of the true eigensystem.

    Note
    ----
    This class does not in *any* way enforce the vectors to be orthogonal. Indeed this class may
    be used to retain values and associated vectors and use it similarly.
    """

    def __init__(self, e, v, parent=None, **info):
        """ Define an eigensystem from given eigenvalues, `e`, and eigenvectors, `v`, with a possible parent object

        Parameters
        ----------
        e : array_like
           eigenvalues where ``e[i]`` refers to the i'th eigenvalue
        v : array_like
           eigenvectors with ``v[i, :]`` containing the i'th eigenvector
        parent : obj, optional
           a parent object that defines the origin of the eigensystem, e.g. a `Hamiltonian`
        **info : dict, optional
           an info dictionary that turns into an attribute on the object.
           This `info` may contain anything that may be relevant for the EigenSystem
        """
        self.e = _a.asarray(e).ravel()
        self.v = _a.asarray(v).ravel() # will return v if already a vector/matrix
        # Ensure the shape is fixed
        self.v.shape = (len(self), -1)
        self.parent = parent
        self.info = info

    def __repr__(self):
        """ The string representation of this object """
        s = self.__class__.__name__ + '{{dim: {0}, min: {1}, max: {2}'.format(len(self),
                                                                              self.e.min(), self.e.max())
        if self.parent is None:
            s += '}}'
        else:
            s += '\n {}}}'.format(repr(self.parent).replace('\n', '\n '))
        return s

    def __len__(self):
        """ Number of eigenvalues/eigenvectors present """
        return len(self.e)

    def size(self):
        """ Size of the eigenvectors. Note the difference from `__len__` """
        return self.v.shape[1]

    def __getitem__(self, key):
        """ Return the eigenvalue and eigenvector associated with the index `key`

        Parameters
        ----------
        key : int or array_like
           the indices for the returned values

        Returns
        -------
        e : array_like
            the eigenvalues at indices `key`
        v : array_like
            the eigenvectors at indices `key`
        """
        key = _a.asarrayi(key)
        es = self.__class__(self.e[key], self.v[key, :], self.parent)
        es.info = self.info
        return es

    def iter(self, only_e=False, only_v=False):
        """ Return an iterator looping over the eigenvalues/vectors in this system

        Parameters
        ----------
        only_e : bool, optional
            Only iterate on the eigenvalues (may be combined with `only_v` to return a tuple)
        only_v : bool, optional
            Only iterate on the eigenvectors (may be combined with `only_e` to return a tuple)

        Yields
        ------
        ev : EigenSystem
           An eigensystem with a single eigenvalue and eigenvector (only if both `only_e` and only_v` are ``False``)
        e : numpy.dtype
           Eigenvalue, only for `only_e` ``True``
        v : array_like
           Eigenvector, only for `only_v` ``True``
        """
        if only_e and only_v:
            for e, v in zip(self.e, self.v):
                yield e, v
        elif only_e:
            for e in self.e:
                yield e
        elif only_v:
            for v in self.v:
                yield v
        else:
            for i in range(len(self)):
                yield self.sub(i)

    def __iter__(self):
        """ Iterator for individual eigensystems """
        for obj in self.iter():
            yield obj

    def copy(self):
        """ Return a copy """
        copy = self.__class__(self.e.copy(), self.v.copy(), self.parent)
        copy.info = self.info
        return copy

    def sort(self, ascending=True):
        """ Sort eigenvalues and eigenvectors (in-place)

        Parameters
        ----------
        ascending : bool, optional
            sort the contained elements ascending, else they will be sorced descending
        """
        if ascending:
            idx = np.argsort(self.e)
        else:
            idx = np.argsort(-self.e)
        self.e = self.e[idx]
        self.v = self.v[idx, :]

    def outer(self, idx=None):
        r""" Return the outer product for the indices `idx` (or all if ``None``) by :math:`\mathbf v \epsilon \mathbf v^{H}` where :math:`H` is the conjugate transpose

        Parameters
        ----------
        idx : int or array_like, optional
           only perform an outer product of the specified indices

        Returns
        -------
        numpy.ndarray : a matrix of size ``(size, size)``
        """
        if idx is None:
            m = _outer(self.e[0], self.v[0, :])
            for i in range(1, len(self)):
                m += _outer(self.e[i], self.v[i, :])
            return m
        idx = _a.asarrayi(idx).ravel()
        m = _outer(self.e[idx[0]], self.v[idx[0], :])
        for i in idx[1:]:
            m += _outer(self.e[i], self.v[i, :])
        return m

    def sub(self, idx):
        """ Return a new eigensystem with only the specified eigenvalues and eigenvectors

        Parameters
        ----------
        idx : int or array_like
            indices that are retained in the returned `EigenSystem`

        Returns
        -------
        EigenSystem
        """
        idx = _a.asarrayi(idx)
        sub = self.__class__(self.e[idx], self.v[idx, :], self.parent)
        sub.info = self.info
        return sub
