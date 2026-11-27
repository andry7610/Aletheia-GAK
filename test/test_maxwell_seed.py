# -*- coding: utf-8 -*-
"""Приёмка уравнений Максвелла на живом каскаде Aletheia-GAK (v1.3)."""
import pytest
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from graph_db import AletheiaMemory
from maxwell_seed import MAXWELL_FIELDS, get_maxwell_laws, MAXWELL_LAWS
from seed_db import CONSTANTS, OPERATORS
from derivation import derive_continuity
from vector_ops import div, rot, ddt


# ------------------------------------------------------------------
# Пространство канона: без подсовывания операторов парсеру
# sympify подхватит SymPy-овскую div(f, g) (полиномиальное деление)
# и упадёт с TypeError. Парсим строго в нашем пространстве.
# ------------------------------------------------------------------
_LOCAL = {
    "div": div, "rot": rot, "ddt": ddt,
    **{n: sp.Symbol(n) for n in ("E", "B", "j", "rho",
                                 "drho_dt", "mu_0", "epsilon_0")},
}
RHO = sp.Symbol("rho")
DRHO = sp.Symbol("drho_dt")


def canon(s: str) -> sp.Expr:
    """Парсинг в каноническом пространстве операторов и символов."""
    return parse_expr(s, local_dict=_LOCAL)


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


# ------------------------------------------------------------------
# Приёмка v1.3: полный Ампер посажен, непрерывность ВЫВОДИТСЯ.
# ВАЖНО: derive_continuity принимает СЫРОЕ выражение закона (lhs - rhs)
# и сам берёт дивергенцию (шаг 0 журнала). Скармливать ему уже взятую
# дивергенцию нельзя — получится бессмысленное div(div(j)).
# Функция возвращает КОРТЕЖ (следствие, журнал шагов).
# ------------------------------------------------------------------

def test_ampere_maxwell_present_v13():
    laws = {name: (lhs, rhs) for name, lhs, rhs in get_maxwell_laws()}
    assert "ampere_maxwell" in laws
    lhs, rhs = laws["ampere_maxwell"]
    assert "ddt(E)" in lhs and "epsilon_0" in lhs and rhs == "0"


def test_old_ampere_marked_stationary():
    desc = MAXWELL_LAWS["ampere_no_displacement"]["description"]
    assert "СТАЦИОНАРНОЕ" in desc.upper()


def test_continuity_derived_from_full_ampere():
    expr = canon("rot(B) - mu_0*(j + epsilon_0*ddt(E))")
    result, log = derive_continuity(expr, vector_fields=["j", "E"])
    expected = canon("drho_dt + div(j)")
    assert result != 0, f"слой вернул пустоту, журнал: {log}"
    # Уравнение A*x = 0 эквивалентно x = 0 при любом ненулевом скаляре A,
    # поэтому допускаем произвольный ненулевой скалярный множитель.
    ratio = sp.simplify(result / expected)
    assert not (ratio.has(div) or ratio.has(ddt)), \
        f"непрерывность не вывелась: {result}\nжурнал: {log}"


def test_continuity_not_derived_from_old_ampere():
    expr = canon("rot(B) - mu_0*j")
    result, log = derive_continuity(expr, vector_fields=["j", "E"])
    assert result != 0, f"слой вернул пустоту, журнал: {log}"
    # из стационарного Ампера производная плотности заряда НЕ возникает —
    # база умеет отказываться выводить то, что не следует
    assert not result.has(DRHO) and not result.has(ddt(RHO)), \
        f"из старого Ампера вывелась непрерывность?! {result}"
