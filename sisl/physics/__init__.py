"""
======================================
Physical objects (:mod:`sisl.physics`)
======================================

.. module:: sisl.physics

Implementations of various DFT and tight-binding related quantities
are defined. The implementations range from simple Brillouin zone
perspectives to self-energy calculations from Hamiltonians.

In `sisl` the general usage of physical matrices are considering sparse
matrices. Hence Hamiltonians, density matrices, etc. are considered
sparse. There are exceptions, but it is generally advisable to have this in mind.

Brillouin zone
==============

.. autosummary::
   :toctree:

   BrillouinZone - base class
   MonkhorstPack - MP class
   BandStructure - bandstructure class

Spin configurations
===================

.. autosummary::
   :toctree:

   Spin - spin configurations

Sparse matrices
===============

.. autosummary::
   :toctree:

   SparseOrbitalBZ - sparse orbital matrix with k-dependent properties
   SparseOrbitalBZSpin - sparse orbital matrix with k-dependent properties and spin configuration


Physical quantites
==================

.. autosummary::
   :toctree:

   EnergyDensityMatrix
   DensityMatrix
   Hamiltonian
   EigenState
   Hessian
   SelfEnergy
   SemiInfinite
   RecursiveSI


States
======

.. autosummary::
   :toctree:

   State
   CoeffState

Distribution functions
======================

.. autosummary::
   :toctree:

   distribution
   gaussian
   lorentzian

"""
from .distribution_function import *
from .brillouinzone import *
from .spin import *
from .sparse import *
from .state import *


from .energydensitymatrix import *
from .densitymatrix import *
from .hamiltonian import *
from .hessian import *
from .self_energy import *

__all__ = [s for s in dir() if not s.startswith('_')]
