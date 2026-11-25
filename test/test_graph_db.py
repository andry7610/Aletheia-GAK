"""Тесты каскадной алгебраической проверки (graph_db.py).

Покрывают патч v1.1 от Алечки: сверка тождества ЦЕЛЫХ уравнений
вместо сравнения частей. Четыре обещанных кейса + регрессия hbar.
"""
import pytest

from graph_db import AletheiaMemory


@pytest.fixture()
def mem():
    m = AletheiaMemory()
    for name, dim in [
        ("E", "energy"),
        ("m", "mass"),
        ("c", "speed"),
        ("J", "current_density"),
        ("f", "frequency"),
        ("h", "action"),
        ("hbar", "action"),
    ]:
        m.add_quantity(name, dim)
    m.add_law("mass_energy", "E", "m*c**2")
    m.add_law("photon_energy", "E", "h*f")
    m.add_law("zero_flux", "0", "J")
    return m


def test_reversed_form_passes(mem):
    """m = E/c^2 эквивалентно канону E = m*c^2 (умножение на 1/c^2)."""
    ok, msg = mem.check_algebraic_law("m", "E/c**2", "mass_energy")
    assert ok, f"перевёрнутая форма должна проходить, получено: {msg}"


def test_swapped_sides_passes(mem):
    """Обмен сторон и перенос слагаемых: m*c^2 = E — тоже канон."""
    ok, msg = mem.check_algebraic_law("m*c**2", "E", "mass_energy")
    assert ok, f"обмен сторон должен проходить, получено: {msg}"


def test_zero_side_canon(mem):
    """Канон 0 = J: верное предложение проходит, неверное — валится."""
    ok, msg = mem.check_algebraic_law("0", "J", "zero_flux")
    assert ok, f"тождественный ноль должен проходить, получено: {msg}"
    ok, msg = mem.check_algebraic_law("f", "0", "zero_flux")
    assert not ok, "f = 0 не должен проходить против канона 0 = J"


def test_zero_canon_rejects_garbage(mem):
    """Знаменитая дыра крест-накрест: при нулевом каноне всё проходило бы."""
    ok, msg = mem.check_algebraic_law("E*c", "0", "zero_flux")
    assert not ok, "произвольное выражение не должно проходить против 0 = J"


def test_wrong_multiplier_fails(mem):
    """m = E/c^3 — честный FAIL против канона E = m*c^2."""
    ok, msg = mem.check_algebraic_law("m", "E/c**3", "mass_energy")
    assert not ok, "E/c^3 не должен проходить против канона E = m*c^2"


def test_unknown_symbol_clear_feedback(mem):
    """Неизвестный символ zeta — внятный фидбек, а не падение парсера."""
    ok, msg = mem.check_algebraic_law("zeta", "E", "mass_energy")
    assert not ok
    assert "zeta" in msg, f"фидбек должен называть символ: {msg}"
    assert "add_quantity" in msg, f"фидбек должен подсказать решение: {msg}"


def test_hbar_hallucination_caught(mem):
    """Классика README: E = hbar*f (без 2*pi) — FAIL, E = h*f — PASS."""
    ok, msg = mem.check_algebraic_law("E", "hbar*f", "photon_energy")
    assert not ok, "E = hbar*f должен ловиться (потерян 2*pi)"
    ok, msg = mem.check_algebraic_law("E", "h*f", "photon_energy")
    assert ok, f"E = h*f должен проходить, получено: {msg}"
    # а форма 2*pi*hbar*f эквивалентна h*f — тоже PASS
    ok, msg = mem.check_algebraic_law("E", "2*pi*hbar*f", "photon_energy")
    assert ok, f"2*pi*hbar*f эквивалентен h*f, получено: {msg}"
