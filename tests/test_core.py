"""
Test the core impedance module.
"""

from typing import cast
import math

import pytest
from pytest import approx
from fastz.core import R, L, C, SeriesZ, ParallelZ, CompositeZ
import numpy as np


class TestR:
    def test_label(self):
        subs = 'test'
        assert R(subs).label == f"R{subs}"

    def test_unit(self):
        value = 50.0
        assert f"{value}Ω" in str(R(v=value))

    def test_frequency_response(self):
        value = 50.0
        f = 42e3
        ff = np.logspace(1, 10, 1000)
        r = R(v=value)
        assert r(f) == approx(value)
        assert r(ff) == approx(np.ones_like(ff) * value)


class TestL:
    def test_label(self):
        subs = 'test'
        assert L(subs).label == f"L{subs}"

    def test_unit(self):
        value = 2e-6
        assert f"{value}H" in str(L(v=value))

    def test_frequency_response(self):
        value = 1e-6
        f = 42e3
        ff = np.logspace(1, 10, 1000)
        l = L(v=value)
        assert l(f) == approx(1j*2*np.pi*f*value)
        assert l(ff) == approx(1j*2*np.pi*ff*value)


class TestC:
    def test_label(self):
        subs = 'test'
        assert C(subs).label == f"C{subs}"

    def test_unit(self):
        value = 2e-9
        assert f"{value}F" in str(C(v=value))

    def test_frequency_response(self):
        value = 1e-9
        f = 42e3
        ff = np.logspace(1, 10, 1000)
        c = C(v=value)
        assert c(f) == approx(1/(1j*2*np.pi*f*value))
        assert c(ff) == approx(1/(1j*2*np.pi*ff*value))


class TestLumpedElement:
    def test_subz(self):
        c = C('a', v=1e-9)
        assert c == c.subz('Ca')
        with pytest.raises(KeyError):
            c.subz('Cb')


class TestSeriesZ:
    def test_1element(self):
        with pytest.raises(ValueError):
            SeriesZ(C())

    def test_2element(self):
        c = C()
        l = L()
        z1 = SeriesZ(c, l, subscript='1')
        assert set(z1._children) == {c, l}

    def test_3element(self):
        c = C()
        l = L()
        r = R()
        z1 = SeriesZ(c, l, r, subscript='1')
        assert set(z1._children) == {c, l, r}

    def test_merge(self):
        r1, r2 = R('1'), R('2')
        c1, c2 = C('1'), C('2')
        zs1 = SeriesZ(r1, c1)
        zs2 = SeriesZ(r2, c2)
        zs1.merge(zs2)
        assert set(zs1._children) == {r1, c1, r2, c2}

    def test_frequency_response(self):
        r, l, c = R(v=10), L(v=100e-6), C(v=1e-6)
        zs = SeriesZ(r, l, c, subscript='s')
        f = 1 / 2 / math.pi / math.sqrt(l.value * c.value)
        ff = np.logspace(4, 6, 5000)
        assert zs(f) == approx(r(f) + l(f) + c(f))
        assert zs(ff) == approx(r(ff) + l(ff) + c(ff))


class TestParallelZ:
    def test_1element(self):
        with pytest.raises(ValueError):
            ParallelZ(C())

    def test_2element(self):
        c = C()
        l = L()
        z1 = ParallelZ(c, l, subscript='1')
        assert set(z1._children) == {c, l}

    def test_3element(self):
        c = C()
        l = L()
        r = R()
        z1 = ParallelZ(c, l, r, subscript='1')
        assert set(z1._children) == {c, l, r}

    def test_merge(self):
        r1, r2 = R('1'), R('2')
        c1, c2 = C('1'), C('2')
        zp1 = ParallelZ(r1, c1)
        zp2 = ParallelZ(r2, c2)
        zp1.merge(zp2)
        assert set(zp1._children) == {r1, c1, r2, c2}

    def test_frequency_response(self):
        r, l, c = R(v=10), L(v=100e-6), C(v=1e-6)
        zs = ParallelZ(r, l, c, subscript='s')
        f = 1 / 2 / math.pi / math.sqrt(l.value * c.value)
        ff = np.logspace(4, 6, 5000)
        assert zs(f) == approx(1/(1/r(f) + 1/l(f) + 1/c(f)))
        assert zs(ff) == approx(1/(1/r(ff) + 1/l(ff) + 1/c(ff)))


class TestCompositeZ:
    def test_subz(self):
        l = L()
        r = R()
        c = C()
        zp = ParallelZ(r, c, subscript='p')
        z1 = SeriesZ(l, zp, subscript='1')
        assert z1.subz('Z1') == z1
        assert z1.subz('Zp') == zp
        assert z1.subz('L') == l
        with pytest.raises(KeyError):
            z1.subz('Zx')

    def test_parallelseries_3element(self):
        r, l, c = R(), L(), C()
        zs = SeriesZ(r, c, subscript='s')
        zps = ParallelZ(zs, l, subscript='ps')
        assert set(zps._children) == {zs, l}
        assert set(cast(CompositeZ, zps.subz('Zs'))._children) == {r, c}

    def test_parallelseries_4element(self):
        la, lb = L('a'), L('b')
        ca, cb = C('a'), C('b')
        zsa = SeriesZ(la, ca, subscript='sa')
        zsb = SeriesZ(lb, cb, subscript='sb')
        zps = ParallelZ(zsa, zsb)
        assert set(zps._children) == {zsa, zsb}
        assert set(cast(CompositeZ, zps.subz('Zsa'))._children) == {la, ca}
        assert set(cast(CompositeZ, zps.subz('Zsb'))._children) == {lb, cb}

    def test_seriesparallel_3element(self):
        r, l, c = R(), L(), C()
        zp = ParallelZ(r, c, subscript='p')
        zsp = SeriesZ(l, zp, subscript='ps')
        assert set(zsp._children) == {l, zp}
        assert set(cast(CompositeZ, zsp.subz('Zp'))._children) == {r, c}

    def test_seriesparallel_4element(self):
        la, lb = L('a'), L('b')
        ca, cb = C('a'), C('b')
        zpa = ParallelZ(la, ca, subscript='pa')
        zpb = ParallelZ(lb, cb, subscript='pb')
        zsp = SeriesZ(zpa, zpb)
        assert set(zsp._children) == {zpa, zpb}
        assert set(cast(CompositeZ, zsp.subz('Zpa'))._children) == {la, ca}
        assert set(cast(CompositeZ, zsp.subz('Zpb'))._children) == {lb, cb}

    def test_merge_dissimilar(self):
        r1, r2 = R('1'), R('2')
        c1, c2 = C('1'), C('2')
        zp = ParallelZ(r1, c1, subscript='p')
        zs = SeriesZ(r2, c2, subscript='s')
        zp.merge(zs)
        assert set(zp._children) == {r1, c1, zs}
        assert set(cast(CompositeZ, zp.subz('Zs'))._children) == {r2, c2}


class TestZ:
    def test_series(self):
        r, l, c = R(), L(), C()
        zs = r + l + c
        assert type(zs) is SeriesZ
        assert set(cast(SeriesZ, zs)._children) == {r, l, c}

    def test_parallel(self):
        r, l, c = R(), L(), C()
        zp = r // l // c
        assert type(zp) is ParallelZ
        assert set(cast(ParallelZ, zp)._children) == {r, l, c}

    def test_seriesparallel(self):
        r, l, c = R(), L(), C()
        zs = (r // l)['p'] + c
        assert type(zs) is SeriesZ
        assert set(cast(SeriesZ, zs)._children) == {zs.subz('Zp'), c}
        assert type(zs.subz('Zp')) is ParallelZ
        assert set(cast(ParallelZ, zs.subz('Zp'))._children) == {r, l}

    def test_parallelseries(self):
        r, l, c = R(), L(), C()
        zp = (r + l)['s'] // c
        assert type(zp) is ParallelZ
        assert set(cast(ParallelZ, zp)._children) == {zp.subz('Zs'), c}
        assert type(zp.subz('Zs')) is SeriesZ
        assert set(cast(ParallelZ, zp.subz('Zs'))._children) == {r, l}

    def test_subscript(self):
        zp = ((R() // L() // C())['p'] + R('1') + L('1') + C('1'))['1']
        assert zp.subscript == '1'
        assert zp.subz('Zp').subscript == 'p'
        assert zp.subz('R1').subscript == '1'

    def test_breakfreq(self):
        r, l, c = R(v=10), L(v=100e-6), C(v=1e-6)
        z1 = (r + l + c)['s'] // C('1', v=10e-6)
        with pytest.raises(ValueError):
            z1.breakfreq('L')
        with pytest.raises(ValueError):
            z1.breakfreq('R R')
        with pytest.raises(ValueError):
            z1.breakfreq('R L C')
        with pytest.raises(ValueError):
            z1.breakfreq('Zs C1')
        assert z1.breakfreq('R C') == approx(1/2/math.pi/r.value/c.value)
        assert z1.breakfreq('R L') == approx(r.value/2/math.pi/l.value)
        assert z1.breakfreq('L C') == approx(1/2/math.pi/math.sqrt(l.value * c.value))
