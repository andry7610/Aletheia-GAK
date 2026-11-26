# -*- coding: utf-8 -*-
"""Тесты векторной алгебры Aletheia-GAK (v1.2): grad/div/rot/ddt, ранги, СИ."""
import pytest
import sympy as sp

from vector_ops import (
    RankChecker, AletheiaTypeError, grad, div, rot, ddt,
    _units_equal, BASE_UNITS,
)

rc = RankChecker()
E, B, rho, j, phi = sp.symbols("E B rho j phi")
epsilon_0, mu_0 = sp.symbols("epsilon_0 mu_0")
V, C, T, F, A, m, s = sp.symbols("V C T F A m s")


# ---------- старые 14 ----------

def test_grad_of_scalar_is_vector():
    r = rc.check(grad(phi))
    assert r.rank == 1
    assert _units_equal(r.unit, V / m)


def test_grad_of_vector_raises():
    with pytest.raises(AletheiaTypeError):
        rc.check(grad(E))


def test_div_of_vector_is_scalar():
    r = rc.check(div(E))
    assert r.rank == 0
    assert _units_equal(r.unit, V / m**2)


def test_div_of_scalar_raises():
    with pytest.raises(AletheiaTypeError):
        rc.check(div(rho))


def test_rot_of_vector_is_vector():
    r = rc.check(rot(E))
    assert r.rank == 1
    assert _units_equal(r.unit, V / m**2)


def test_rot_alias_curl():
    r1 = rc.check_text("rot(E)")
    r2 = rc.check_text("curl(E)")
    assert r1.rank == r2.rank == 1
    assert _units_equal(r1.unit, r2.unit)


def test_scalar_times_vector_ok():
    r = rc.check(mu_0 * j)
    assert r.rank == 1
    assert r.nonlinear is False


def test_product_two_fields_raises():
    with pytest.raises(AletheiaTypeError):
        rc.check(E * B)


def test_nested_grad_raises():
    with pytest.raises(AletheiaTypeError):
        rc.check(grad(grad(phi)))


def test_unknown_symbol_raises():
    with pytest.raises(AletheiaTypeError):
        rc.check(sp.Symbol("Q") * E)


def test_base_units_faraday_equivalence():
    assert _units_equal(V / m**2, T / s)


def test_base_units_negative_case():
    assert not _units_equal(V / m, T)


def test_check_text_forbids_dunder():
    with pytest.raises(AletheiaTypeError):
        rc.check_text("__import__('os').getcwd()")


def test_check_text_is_sandboxed():
    with pytest.raises(AletheiaTypeError):
        rc.check_text("open('secret.txt')")


# ---------- новые 8: оператор ddt ----------

def test_ddt_of_vector_field():
    r = rc.check(ddt(B))
    assert r.rank == 1
    assert _units_equal(r.unit, T / s)


def test_ddt_of_scalar_field():
    r = rc.check(ddt(rho))
    assert r.rank == 0
    # C/(m^3 * s) == A/m^3
    assert _units_equal(r.unit, A / m**3)


def test_ddt_linear_with_constant():
    r = rc.check(epsilon_0 * ddt(E))
    assert r.rank == 1
    assert r.nonlinear is False


def test_faraday_structure_passes():
    r = rc.check(rot(E) + ddt(B))
    assert r.rank == 1
    assert r.nonlinear is False


def test_ampere_structure_passes():
    r = rc.check(rot(B) - mu_0 * j)
    assert r.rank == 1
    assert r.nonlinear is False


def test_gauss_structure_passes():
    r = rc.check(div(E) - rho / epsilon_0)
    assert r.rank == 0
    assert r.nonlinear is False


def test_ddt_nonlinear_propagates():
    r = rc.check(ddt(rho * phi))
    assert r.nonlinear is True


def test_check_text_faraday():
    r = rc.check_text("rot(E) + ddt(B)")
    assert r.rank == 1
