from __future__ import print_function, division

import numpy as np
from numpy import in1d, argsort

# Import sile objects
from ..sile import add_sile
from ._cdf import _devncSileTBtrans
from sisl.utils import *
import sisl._array as _a

# Import the geometry object
from sisl.unit.siesta import unit_convert


__all__ = ['tbtsencSileTBtrans', 'phtsencSileTBtrans']


Bohr2Ang = unit_convert('Bohr', 'Ang')
Ry2eV = unit_convert('Ry', 'eV')


class tbtsencSileTBtrans(_devncSileTBtrans):
    r""" TBtrans self-energy file object with downfolded self-energies to the device region

    The :math:`\Sigma` object contains all self-energies on the specified k- and energy grid projected
    into the device region.

    This is mainly an output file object from TBtrans and can be used as a post-processing utility for
    testing various things in Python.

    Note that *anything* returned from this object are the self-energies in eV.

    Examples
    --------
    >>> H = Hamiltonian(device) # doctest: +SKIP
    >>> se = tbtsencSileTBtrans(...) # doctest: +SKIP
    >>> # Return the self-energy for the left electrode (unsorted)
    >>> se_unsorted = se.self_energy('Left', 0.1, [0, 0, 0]) # doctest: +SKIP
    >>> # Return the self-energy for the left electrode (sorted)
    >>> se_sorted = se.self_energy('Left', 0.1, [0, 0, 0], sort=True) # doctest: +SKIP
    >>> #
    >>> # Query the indices in the full Hamiltonian
    >>> pvt_unsorted = se.pivot('Left').reshape(-1, 1) # doctest: +SKIP
    >>> pvt_sorted = se.pivot('Left', sort=True).reshape(-1, 1) # doctest: +SKIP
    >>> # The following two lines are equivalent
    >>> Hfull[pvt_unsorted, pvt_unsorted.T] -= se_unsorted[:, :] # doctest: +SKIP
    >>> Hfull[pvt_sorted, pvt_sorted.T] -= se_sorted[:, :] # doctest: +SKIP
    >>> # Query the indices in the device Hamiltonian
    >>> dpvt_unsorted = se.pivot('Left', in_device=True).reshape(-1, 1) # doctest: +SKIP
    >>> dpvt_sorted = se.pivot('Left', in_device=True, sort=True).reshape(-1, 1) # doctest: +SKIP
    >>> # Following inserts are equivalent
    >>> Hdev[dpvt_unsorted, dpvt_unsorted.T] -= se_unsorted[:, :] # doctest: +SKIP
    >>> Hdev[dpvt_sorted, dpvt_sorted.T] -= se_sorted[:, :] # doctest: +SKIP
    """

    def o2p(self, orbital):
        """ Return the pivoting indices (0-based) for the orbitals

        Parameters
        ----------
        orbital : array_like or int
           orbital indices (0-based)
        """
        return in1d(self.pivot(), orbital).nonzero()[0]

    def _elec(self, elec):
        """ Converts a string or integer to the corresponding electrode name

        Parameters
        ----------
        elec : str or int
           if `str` it is the *exact* electrode name, if `int` it is the electrode
           index

        Returns
        -------
        str : the electrode name
        """
        try:
            elec = int(elec)
            return self.elecs[elec]
        except:
            return elec

    @property
    def elecs(self):
        """ List of electrodes """
        return list(self.groups.keys())

    def chemical_potential(self, elec):
        """ Return the chemical potential associated with the electrode `elec` """
        return self._value('mu', self._elec(elec))[0] * Ry2eV
    mu = chemical_potential

    def eta(self, elec):
        """ The imaginary part used when calculating the self-energies in eV """
        try:
            return self._value('eta', self._elec(elec))[0] * Ry2eV
        except:
            return 0.

    def pivot(self, elec=None, in_device=False, sort=False):
        """ Return the pivoting indices for a specific electrode

        Parameters
        ----------
        elec : str or int
           the corresponding electrode to return the self-energy from
        in_device : bool, optional
           If ``True`` the pivoting table will be translated to the device region orbitals
        sort : bool, optional
           Whether the returned indices are sorted. Mostly useful if the self-energies are returned
           sorted as well.

        Examples
        --------
        >>> se = tbtsencSileTBtrans(...) # doctest: +SKIP
        >>> se.pivot() # doctest: +SKIP
        [3, 4, 6, 5, 2]
        >>> se.pivot(sort=True) # doctest: +SKIP
        [2, 3, 4, 5, 6]
        >>> se.pivot(0) # doctest: +SKIP
        [2, 3]
        >>> se.pivot(0, in_device=True) # doctest: +SKIP
        [4, 0]
        >>> se.pivot(0, in_device=True, sort=True) # doctest: +SKIP
        [0, 1]
        >>> se.pivot(0, sort=True) # doctest: +SKIP
        [2, 3]
        """
        if elec is None:
            if in_device and sort:
                pvt = _a.arangei(self.no_d)
            pvt = self._value('pivot') - 1
            if in_device:
                # Count number of elements that we need to subtract from each orbital
                subn = _a.onesi(self.no)
                subn[pvt] = 0
                pvt -= _a.cumsumi(subn)[pvt]
            elif sort:
                pvt = np.sort(pvt)
            return pvt

        if in_device:
            pvt = self._value('pivot') - 1
            if sort:
                pvt = np.sort(pvt)

        # Get electrode pivoting elements
        se_pvt = self._value('pivot', tree=self._elec(elec)) - 1
        if sort:
            # Sort pivoting indices
            # Since we know that pvt is also sorted, then
            # the resulting in_device would also return sorted
            # indices
            se_pvt = np.sort(se_pvt)

        if in_device:
            # translate to the device indices
            se_pvt = in1d(pvt, se_pvt, assume_unique=True).nonzero()[0]
        return se_pvt

    def self_energy(self, elec, E, k, sort=False):
        """ Return the self-energy from the electrode `elec`

        Parameters
        ----------
        elec : str or int
           the corresponding electrode to return the self-energy from
        E : float or int
           energy to retrieve the self-energy at, if a floating point the closest
           energy value will be found and returned, if an integer it will correspond
           to the exact index
        k : array_like or int
           k-point to retrieve, if an integer it is the k-index in the file
        sort : bool, optional
           if ``True`` the returned self-energy will be sorted (equivalent to pivoting the self-energy)
        """
        tree = self._elec(elec)
        ik = self.kindex(k)
        iE = self.Eindex(E)

        re = self._variable('ReSelfEnergy', tree=tree)
        im = self._variable('ImSelfEnergy', tree=tree)

        SE = (re[ik, iE, :, :] + 1j * im[ik, iE, :, :]) * Ry2eV
        if sort:
            pvt = self.pivot(elec)
            idx = argsort(pvt)
            idx.shape = (-1, 1)

            # pivot for sorted device region
            return SE[idx, idx.T]

        return SE

    def self_energy_average(self, elec, E, sort=False):
        """ Return the k-averaged average self-energy from the electrode `elec`

        Parameters
        ----------
        elec : str or int
           the corresponding electrode to return the self-energy from
        E : float or int
           energy to retrieve the self-energy at, if a floating point the closest
           energy value will be found and returned, if an integer it will correspond
           to the exact index
        sort : bool, optional
           if ``True`` the returned self-energy will be sorted but not necessarily consecutive
           in the device region.
        """
        tree = self._elec(elec)
        iE = self.Eindex(E)

        re = self._variable('ReSelfEnergyMean', tree=tree)
        im = self._variable('ImSelfEnergyMean', tree=tree)

        SE = (re[ik, iE, :, :] + 1j * im[ik, iE, :, :]) * Ry2eV
        if sort:
            pvt = self.pivot(elec)
            idx = argsort(pvt)
            idx.shape = (-1, 1)

            # pivot for sorted device region
            return SE[idx, idx.T]

        return SE


add_sile('TBT.SE.nc', tbtsencSileTBtrans)
# Add spin-dependent files
add_sile('TBT_UP.SE.nc', tbtsencSileTBtrans)
add_sile('TBT_DN.SE.nc', tbtsencSileTBtrans)


class phtsencSileTBtrans(tbtsencSileTBtrans):
    """ PHtrans file object """
    _trans_type = 'PHT'

add_sile('PHT.SE.nc', phtsencSileTBtrans)
