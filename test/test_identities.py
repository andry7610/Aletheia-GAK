# -*- coding: utf-8 -*-
"""Тесты слоя тождеств Aletheia-GAK (v1.2): div(rot)=0, rot(grad)=0."""
import pytest
import sympy as sp

from identities import IdentitySimplifier, simplify_identities
from vector_ops import RankChecker, AletheiaTypeError, div, rot, grad, curl

B, E, phi = sp.symbols("B E phi")
ids = IdentitySimplifier()


def test_div_rot_collapse():
    expr = div(rot(B))
    assert simplify_identities(expr) == sp.S.Zero


def test_rot_grad_collapse():
    expr = rot(grad(phi))
    assert simplify_identities(expr) == sp.S.Zero


def test_curl_alias_collapse():
    expr = div(curl(B))
    assert simplify_identities(expr) == sp.S.Zero


def test_scalar_multiplier_collapse():
    expr = div(3 * rot(B))
    assert simplify_identities(expr) == sp.S.Zero


def test_div_grad_not_collapsed():
    expr = div(grad(phi))
    assert simplify_identities(expr) == expr  # не тождество - не трогаем


def test_rot_rot_not_collapsed():
    expr = rot(rot(B))
    assert simplify_identities(expr) == expr  # не тождество - не трогаем


def test_embedded_in_sum():
    expr = div(E) + div(rot(B))
    simplified = simplify_identities(expr)
    assert simplified == div(E)  # нулевой член схлопнулся, остальное цело


def test_check_text_full_pipeline():
    r, expr = ids.check_text("div(rot(B))")
    assert r.rank == 0
    assert r.unit == 1  # безразмерный ноль


def test_identity_layer_does_not_eat_foreign_errors():
    # тождества не маскируют ошибки типов: div(rho) по-прежнему рубится
    with pytest.raises(AletheiaTypeError):
        ids.check_text("div(rho)")
