"""
Test the core impedance module.
"""

import pytest
from fastz.core import R, L, C
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
        assert r(f) == value
        assert np.array_equal(r(ff), np.ones_like(ff) * value)


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
        assert l(f) == 1j*2*np.pi*f*value
        assert np.array_equal(l(ff), 1j*2*np.pi*ff*value)


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
        assert c(f) == 1/(1j*2*np.pi*f*value)
        assert np.array_equal(c(ff), 1/(1j*2*np.pi*ff*value))

