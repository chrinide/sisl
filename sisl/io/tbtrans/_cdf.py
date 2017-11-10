from __future__ import print_function, division

import warnings
from numbers import Integral

import numpy as np
from numpy import in1d

# Import sile objects
from ..sile import sile_raise_write
from .sile import SileCDFTBtrans
from sisl.utils import *
import sisl._array as _a

# Import the geometry object
from sisl import Geometry, Atom, Atoms, SuperCell
from sisl._help import _str, ensure_array
from sisl.unit.siesta import unit_convert

__all__ = ['_ncSileTBtrans', '_devncSileTBtrans']


Bohr2Ang = unit_convert('Bohr', 'Ang')
Ry2eV = unit_convert('Ry', 'eV')
Ry2K = unit_convert('Ry', 'K')
eV2Ry = unit_convert('eV', 'Ry')


class _ncSileTBtrans(SileCDFTBtrans):
    r""" Common TBtrans NetCDF file object due to a lot of the files having common entries

    This enables easy read of the Geometry and SuperCells etc.
    """

    def _setup(self, *args, **kwargs):
        """ Setup the special object for data containing """
        self._data = dict()

        if self._access > 0:

            # Fake double calls
            access = self._access
            self._access = 0

            # There are certain elements which should
            # be minimal on memory but allow for
            # fast access by the object.
            for d in ['cell', 'xa', 'lasto', 'E']:
                self._data[d] = self._value(d)
            # tbtrans does not store the k-points and weights
            # if the Gamma-point is used.
            try:
                self._data['kpt'] = self._value('kpt')
            except:
                self._data['kpt'] = _a.zerosd([3])
            try:
                self._data['wkpt'] = self._value('wkpt')
            except:
                self._data['wkpt'] = _a.onesd([1])

            # Create the geometry in the data file
            self._data['_geom'] = self.read_geometry()

            # Reset the access pattern
            self._access = access

    def read_supercell(self):
        """ Returns `SuperCell` object from this file """
        cell = _a.arrayd(np.copy(self.cell))
        cell.shape = (3, 3)

        try:
            nsc = self._value('nsc')
        except:
            nsc = None

        sc = SuperCell(cell, nsc=nsc)
        try:
            sc.sc_off = self._value('isc_off')
        except:
            # This is ok, we simply do not have the supercell offsets
            pass

        return sc

    def read_geometry(self, *args, **kwargs):
        """ Returns `Geometry` object from this file """
        sc = self.read_supercell()

        xyz = _a.arrayd(np.copy(self.xa))
        xyz.shape = (-1, 3)

        # Create list with correct number of orbitals
        lasto = _a.arrayi(np.copy(self.lasto) + 1)
        nos = np.append([lasto[0]], np.diff(lasto))
        nos = _a.arrayi(nos)

        if 'atom' in kwargs:
            # The user "knows" which atoms are present
            atms = kwargs['atom']
            # Check that all atoms have the correct number of orbitals.
            # Otherwise we will correct them
            for i in range(len(atms)):
                if atms[i].orbs != nos[i]:
                    atms[i] = Atom(Z=atms[i].Z, orbs=nos[i], tag=atms[i].tag)

        else:
            # Default to Hydrogen atom with nos[ia] orbitals
            # This may be counterintuitive but there is no storage of the
            # actual species
            atms = [Atom(Z='H', orbs=o) for o in nos]

        # Create and return geometry object
        geom = Geometry(xyz, atms, sc=sc)

        return geom

    def write_geometry(self, *args, **kwargs):
        """ This is not meant to be used """
        raise ValueError(self.__class__.__name__ + " can not write a geometry")

    # This class also contains all the important quantities elements of the
    # file.

    @property
    def geometry(self):
        """ The associated geometry from this file """
        return self.read_geometry()
    geom = geometry

    @property
    def cell(self):
        """ Unit cell in file """
        return self._value('cell') * Bohr2Ang

    @property
    def na(self):
        """ Returns number of atoms in the cell """
        return len(self._dimension('na_u'))
    na_u = na

    @property
    def no(self):
        """ Returns number of orbitals in the cell """
        return len(self._dimension('no_u'))
    no_u = no

    @property
    def xyz(self):
        """ Atomic coordinates in file """
        return self._value('xa') * Bohr2Ang
    xa = xyz

    @property
    def lasto(self):
        """ Last orbital of corresponding atom """
        return self._value('lasto') - 1

    @property
    def k(self):
        """ Sampled k-points in file """
        return self._value('kpt')
    kpt = k

    @property
    def wk(self):
        """ Weights of k-points in file """
        return self._value('wkpt')
    wkpt = wk

    @property
    def nk(self):
        """ Number of k-points in file """
        return len(self.dimensions['nkpt'])
    nkpt = nk

    @property
    def E(self):
        """ Sampled energy-points in file """
        return self._value('E') * Ry2eV

    @property
    def ne(self):
        """ Number of energy-points in file """
        return len(self._dimension('ne'))
    nE = ne

    def Eindex(self, E):
        """ Return the closest energy index corresponding to the energy ``E``

        Parameters
        ----------
        E : float or int
           if ``int``, return it-self, else return the energy index which is
           closests to the energy.
        """
        if isinstance(E, Integral):
            return E
        elif isinstance(E, _str):
            # This will always be converted to a float
            E = float(E)
        idxE = np.abs(self.E - E).argmin()
        ret_E = self.E[idxE]
        if abs(ret_E - E) > 1e-3:
            warnings.warn(self.__class__.__name__ + " requesting energy " +
                          "{0:.5f} eV, found {1:.5f} eV as the closest energy!".format(E, ret_E),
                          UserWarning)
        return idxE

    def kindex(self, k):
        """ Return the index of the k-point that is closests to the queried k-point (in reduced coordinates)

        Parameters
        ----------
        k : array_like of float
           the queried k-point in reduced coordinates :math:`]-0.5;0.5]`.
        """
        ik = np.sum(np.abs(self.k - _a.asarrayd(k)[None, :]), axis=1).argmin()
        ret_k = self.k[ik, :]
        if not np.allclose(ret_k, k, atol=0.0001):
            warnings.warn(self.__class__.__name__ + " requesting k-point " +
                          "[{0:.3f}, {1:.3f}, {2:.3f}]".format(*k) +
                          " found " +
                          "[{0:.3f}, {1:.3f}, {2:.3f}]".format(*ret_k),
                          UserWarning)
        return ik


class _devncSileTBtrans(_ncSileTBtrans):
    r""" Common TBtrans NetCDF file object due to a lot of the files having common entries

    This one also enables device region atoms and pivoting tables.
    """

    def _setup(self, *args, **kwargs):
        """ Setup the special object for data containing """
        super(_ncSileTBtrans, self)._setup(*args, **kwargs)

        if self._access > 0:

            # Fake double calls
            access = self._access
            self._access = 0

            # There are certain elements which should
            # be minimal on memory but allow for
            # fast access by the object.
            for d in ['a_dev', 'pivot']:
                self._data[d] = self._value(d)

            # Reset the access pattern
            self._access = access

    # Device atoms and other quantities
    @property
    def na_d(self):
        """ Number of atoms in the device region """
        return len(self._dimension('na_d'))
    na_dev = na_d

    @property
    def a_dev(self):
        """ Atomic indices (0-based) of device atoms """
        return self._value('a_dev') - 1

    @property
    def no_d(self):
        """ Number of orbitals in the device region """
        return len(self.dimensions['no_d'])

    def pivot(self):
        """ Pivoting orbitals for the full system """
        return self._value('pivot') - 1

    def a2p(self, atom):
        """ Return the pivoting indices (0-based) for the atoms

        Parameters
        ----------
        atom : array_like or int
           atomic indices (0-based)
        """
        orbs = self.geom.a2o(atom, True)
        return self.o2p(orbs)

    def o2p(self, orbital):
        """ Return the pivoting indices (0-based) for the orbitals

        Parameters
        ----------
        orbital : array_like or int
           orbital indices (0-based)
        """
        return in1d(self.pivot, orbital).nonzero()[0]