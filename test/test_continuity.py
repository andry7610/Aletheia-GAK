"""Тесты Шага 2: уравнение непрерывности с нулевой правой стороной."""

import os
import tempfile

import pytest

from graph_db import AletheiaMemory
from seed_db import OPERATORS


@pytest.fixture()
def memory():
    m = AletheiaMemory()
    for name, dim, desc in OPERATORS:
        m.add_quantity(name, dim, desc)
    m.add_law("continuity_equation", "div_J + drho_dt", "0")
    return m


def test_continuity_canonical_form(memory):
    ok, msg = memory.check_algebraic_law("div_J + drho_dt", "0", "continuity_equation")
    assert ok, msg


def test_continuity_commutative(memory):
    ok, msg = memory.check_algebraic_law("drho_dt + div_J", "0", "continuity_equation")
    assert ok, msg


def test_continuity_scaled(memory):
    ok, msg = memory.check_algebraic_law("2 * div_J + 2 * drho_dt", "0", "continuity_equation")
    assert ok, msg
    assert "множител" in msg


def test_continuity_extra_zero(memory):
    ok, msg = memory.check_algebraic_law("3 * div_J + 3 * drho_dt + 0", "0", "continuity_equation")
    assert ok, msg


def test_continuity_wrong_sign_rejected(memory):
    ok, msg = memory.check_algebraic_law("div_J - drho_dt", "0", "continuity_equation")
    assert not ok


def test_continuity_wrong_coefficient_rejected(memory):
    ok, msg = memory.check_algebraic_law("div_J + 2 * drho_dt", "0", "continuity_equation")
    assert not ok


def test_operator_dimensions_match():
    """Обе стороны уравнения непрерывности имеют размерность A/m**3."""
    dims = {name: dim for name, dim, _ in OPERATORS}
    assert dims["div_J"] == dims["drho_dt"] == "A/m**3"


def test_unknown_operator_gives_feedback(memory):
    """Неизвестный символ не исключение, а внятный отказ с подсказкой."""
    ok, msg = memory.check_algebraic_law("div_J + dphi_dt", "0", "continuity_equation")
    assert not ok
    assert "неизвестные символы" in msg and "dphi_dt" in msg


def test_continuity_law_in_seed():
    """Закон непрерывности реально попадает в базу при populate_knowledge_base."""
    from seed_db import populate_knowledge_base
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        memory = populate_knowledge_base(db_path=path)
        cursor = memory.conn.cursor()
        cursor.execute("SELECT lhs, rhs FROM laws WHERE name = ?", ("continuity_equation",))
        row = cursor.fetchone()
        assert row is not None
        assert row["lhs"] == "div_J + drho_dt" and row["rhs"] == "0"
    finally:
        memory.close()
        os.remove(path)
