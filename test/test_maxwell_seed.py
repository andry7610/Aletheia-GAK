# -*- coding: utf-8 -*-
"""Приёмка уравнений Максвелла на живом каскаде Aletheia-GAK (v1.2)."""
import pytest

from graph_db import AletheiaMemory
from maxwell_seed import MAXWELL_FIELDS, get_maxwell_laws
from seed_db import CONSTANTS, OPERATORS


@pytest.fixture
def memory():
    mem = AletheiaMemory(":memory:")
    # константы и операторы — как в реальном populate_knowledge_base,
    # иначе белый список парсера отсечёт epsilon_0, mu_0, div_J, drho_dt
    for _name, _value, dim, desc in CONSTANTS:
        mem.add_quantity(_name, dim, desc)
    for name, dim, desc in OPERATORS:
        mem.add_quantity(name, dim, desc)
    for name, dim, desc in MAXWELL_FIELDS:
        mem.add_quantity(name, dim, desc)
    for name, lhs, rhs in get_maxwell_laws():
        mem.add_law(name, lhs, rhs)
    yield mem
    mem.close()


def test_faraday_canonical(memory):
    ok, msg = memory.check_algebraic_law("rot(E) + ddt(B)", "0", "faraday_law")
    assert ok, msg


def test_faraday_reordered(memory):
    ok, msg = memory.check_algebraic_law("ddt(B) + rot(E)", "0", "faraday_law")
    assert ok, msg


def test_faraday_scaled(memory):
    ok, msg = memory.check_algebraic_law("2*(rot(E) + ddt(B))", "0", "faraday_law")
    assert ok, msg


def test_faraday_identity_eaten(memory):
    ok, msg = memory.check_algebraic_law(
        "rot(E) + ddt(B) + div(rot(B))", "0", "faraday_law"
    )
    assert ok, msg


def test_gauss_e_canonical(memory):
    ok, msg = memory.check_algebraic_law("div(E)", "rho/epsilon_0", "gauss_electric")
    assert ok, msg


def test_gauss_b_canonical(memory):
    ok, msg = memory.check_algebraic_law("div(B)", "0", "gauss_magnetic")
    assert ok, msg


def test_ampere_canonical(memory):
    ok, msg = memory.check_algebraic_law("rot(B)", "mu_0*j", "ampere_no_displacement")
    assert ok, msg


def test_faraday_wrong_term_rejected(memory):
    ok, msg = memory.check_algebraic_law(
        "rot(E) + ddt(B) + mu_0*j", "0", "faraday_law"
    )
    assert not ok


def test_rank_conflict_rejected(memory):
    ok, msg = memory.check_algebraic_law("rot(E) + div(B)", "0", "faraday_law")
    assert not ok


def test_missing_law_gives_feedback(memory):
    ok, msg = memory.check_algebraic_law("div(B)", "0", "no_such_law")
    assert not ok and "не найден" in msg


def test_continuity_regression(memory):
    # регресс v1.1: непрерывность живёт в той же базе и не пострадала
    memory.add_law("continuity_equation", "div_J + drho_dt", "0")
    ok, msg = memory.check_algebraic_law("div_J + drho_dt", "0", "continuity_equation")
    assert ok, msg
