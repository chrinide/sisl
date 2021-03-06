from __future__ import print_function, division

import pytest

from itertools import product
import math as m
import numpy as np

from sisl import Geometry, Atom, SuperCell, SuperCellChild
from sisl import BrillouinZone, BandStructure
from sisl import MonkhorstPack


@pytest.fixture
def setup():
    class t():
        def __init__(self):
            self.s1 = SuperCell(1, nsc=[3, 3, 1])
            self.s2 = SuperCell([2, 2, 10, 90, 90, 60], [5, 5, 1])
    return t()


@pytest.mark.brillouinzone
@pytest.mark.bz
class TestBrillouinZone(object):

    def setUp(self, setup):
        setup.s1 = SuperCell(1, nsc=[3, 3, 1])
        setup.s2 = SuperCell([2, 2, 10, 90, 90, 60], [5, 5, 1])

    def test_bz1(self, setup):
        bz = BrillouinZone(1.)
        repr(bz)
        bz.weight
        bz = BrillouinZone(setup.s1)
        assert len(bz) == 1
        assert np.allclose(bz.tocartesian([0, 0, 0]), [0] * 3)
        assert np.allclose(bz.tocartesian([0.5, 0, 0]), [m.pi, 0, 0])
        assert np.allclose(bz.toreduced([0, 0, 0]), [0] * 3)
        assert np.allclose([0.5, 0, 0], bz.tocartesian(bz.toreduced([0.5, 0, 0])))
        for k in bz:
            assert np.allclose(k, np.zeros(3))

    def test_class1(self, setup):
        class Test(SuperCellChild):
            def __init__(self, sc):
                self.set_supercell(sc)
            def eigh(self, k, *args, **kwargs):
                return np.arange(3)
            def eig(self, k, *args, **kwargs):
                return np.arange(3) - 1
        bz = BrillouinZone(Test(setup.s1))
        repr(bz)
        assert np.allclose(bz.eigh(), np.arange(3))
        assert np.allclose(bz.eig(), np.arange(3)-1)

    def test_class2(self, setup):
        class Test(SuperCellChild):
            def __init__(self, sc):
                self.set_supercell(sc)
            def eigh(self, k, *args, **kwargs):
                return np.arange(3)
            def eig(self, k, *args, **kwargs):
                return np.arange(3) - 1
        bz = BrillouinZone(Test(setup.s1))
        # Try the yield method
        bz.asyield()
        for val in bz.eigh():
            assert np.allclose(val, np.arange(3))
        for val in bz.eig():
            assert np.allclose(val, np.arange(3) - 1)
        # Average
        assert np.allclose(bz.asaverage().eigh(), np.arange(3))
        assert np.allclose(bz.asaverage().eigh(eta=True), np.arange(3))

    def test_class3(self, setup):
        class Test(SuperCellChild):
            def __init__(self, sc):
                self.set_supercell(sc)
            def eigh(self, k, *args, **kwargs):
                return np.arange(3)
            def eig(self, k, *args, **kwargs):
                return np.arange(3) - 1
        bz = MonkhorstPack(Test(setup.s1), [2] * 3)
        # Try the yield method
        bz.asyield()
        for val in bz.eigh():
            assert np.allclose(val, np.arange(3))
        for val in bz.eig():
            assert np.allclose(val, np.arange(3) - 1)
        # Average
        assert np.allclose(bz.asaverage().eigh(), np.arange(3))

    def test_mp1(self, setup):
        bz = MonkhorstPack(setup.s1, [2] * 3, trs=False)
        assert len(bz) == 8
        assert bz.weight[0] == 1. / 8

    def test_mp2(self, setup):
        bz1 = MonkhorstPack(setup.s1, [2] * 3, trs=False)
        assert len(bz1) == 8
        bz2 = MonkhorstPack(setup.s1, [2] * 3, displacement=[.5] * 3, trs=False)
        assert len(bz2) == 8
        assert not np.allclose(bz1.k, bz2.k)

    def test_mp3(self, setup):
        bz1 = MonkhorstPack(setup.s1, [2] * 3, size=0.5, trs=False)
        assert len(bz1) == 8
        assert np.all(bz1.k < 0.25)
        assert bz1.weight.sum() == pytest.approx(0.5 ** 3)

    def test_trs(self, setup):
        size = [0.05, 0.5, 0.9]
        for x, y, z in product(np.arange(10) + 1, np.arange(20) + 1, np.arange(6) + 1):
            bz = MonkhorstPack(setup.s1, [x, y, z])
            assert bz.weight.sum() == pytest.approx(1.)
            bz = MonkhorstPack(setup.s1, [x, y, z], size=size)
            assert bz.weight.sum() == pytest.approx(np.prod(size))

    def test_mp_gamma_centered(self, setup):
        for x, y, z in product(np.arange(10) + 1, np.arange(20) + 1, np.arange(6) + 1):
            bz = MonkhorstPack(setup.s1, [x, y, z], trs=False)
            assert len(bz) == x * y * z
            assert ((bz.k == 0.).sum(1).astype(np.int32) == 3).sum() == 1

    def test_mp_gamma_centered_displ(self, setup):
        for x, y, z in product(np.arange(10) + 1, np.arange(20) + 1, np.arange(6) + 1):
            bz = MonkhorstPack(setup.s1, [x, y, z], displacement=[0.2, 0, 0], trs=False)
            k = bz.k.copy()
            k[:, 0] -= 0.2
            assert len(bz) == x * y * z
            assert ((k == 0.).sum(1).astype(np.int32) == 3).sum() == 1

    def test_pbz1(self, setup):
        bz = BandStructure(setup.s1, [[0]*3, [.5]*3], 300)
        assert len(bz) == 300

        bz2 = BandStructure(setup.s1, [[0]*2, [.5]*2], 300, ['A', 'C'])
        assert len(bz) == 300

        bz3 = BandStructure(setup.s1, [[0]*2, [.5]*2], [150] * 2)
        assert len(bz) == 300
        bz.lineartick()
        bz.lineark()
        bz.lineark(True)

    def test_pbz2(self, setup):
        bz = BandStructure(setup.s1, [[0]*3, [.25]*3, [.5]*3], 300)
        assert len(bz) == 300
