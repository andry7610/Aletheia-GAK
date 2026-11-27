# -*- coding: utf-8 -*-
"""
test_derivation — тесты слоя вывода (v1.3).

Слой вывода получает закон из законов. Ключевой тест:
непрерывность выводится из полного Ампера + Гаусса —
первый в истории проекта ВЫВОД закона, а не сверка с посаженным.

Конвенция канона v1.1: производная скалярного поля — именованный символ
(drho_dt). Если текст канона непрерывности в seed_db.py отличается —
править CANON_CONTINUITY здесь, в одном месте.
"""
import sympy as sp

from vector_ops import div, ddt, rot
from derivation import (
    expand_op_linearly, commute_div_ddt, extract_constants_from_ddt,
    normalize_zero_form, apply_canon_alias, derive_continuity,
    zero_form_matches,
)

CANON_CONTINUITY = "div(j) + drho_dt"
VF = frozenset({"E", "B", "j"})


# ---------- вывод непрерывности ----------

def test_derive_continuity_matches_canon():
    expr, steps = derive_continuity()
    assert zero_form_matches(expr, CANON_CONTINUITY)


def test_derivation_steps_log_complete():
    _, steps = derive_continuity()
    assert len(steps) >= 7                       # журнал не пуст и полон
    assert any("Гаусса" in s for s in steps)     # подстановка Гаусса была
    assert any("псевдоним" in s for s in steps)  # и alias заявлен явно


def test_reordered_canon_matches():
    expr, _ = derive_continuity()
    assert zero_form_matches(expr, "drho_dt + div(j)")


def test_negative_old_ampere_not_enough():
    # Стационарный Ампер НЕ выводит непрерывность: div(j) = 0, а не div(j)+drho_dt = 0
    expr, _ = derive_continuity(ampere_lhs="rot(B) - mu_0*j", ampere_rhs="0")
    assert not zero_form_matches(expr, CANON_CONTINUITY)


# ---------- линейность ----------

def test_expand_linearity_with_vector_fields():
    expr = div(sp.Symbol("mu_0") * (sp.Symbol("E") + 2 * sp.Symbol("B")))
    res = expand_op_linearly(sp.expand(expr), "div", VF)  # как в конвейере
    assert res == (sp.Symbol("mu_0") * div(sp.Symbol("E"))
                   + 2 * sp.Symbol("mu_0") * div(sp.Symbol("B")))


def test_expand_keeps_scalar_expression():
    # div от чисто скалярного выражения не трогается — ранги судит RankChecker
    expr = div(sp.Symbol("k") * sp.Symbol("c"))
    assert expand_op_linearly(expr, "div", VF) == expr


# ---------- коммутация ----------

def test_commutation_div_ddt():
    assert commute_div_ddt(div(ddt(sp.Symbol("E")))) == ddt(div(sp.Symbol("E")))


def test_commutation_does_not_touch_other_ops():
    expr = rot(ddt(sp.Symbol("E")))
    assert commute_div_ddt(expr) == expr


# ---------- константы под ddt ----------

def test_constant_out_of_ddt():
    rho, eps0 = sp.Symbol("rho"), sp.Symbol("epsilon_0")
    res = extract_constants_from_ddt(ddt(rho / eps0), {"epsilon_0"})
    assert res == eps0 ** -1 * ddt(rho)


def test_ddt_of_constant_is_zero():
    res = extract_constants_from_ddt(ddt(sp.Symbol("epsilon_0")), {"epsilon_0"})
    assert res == 0


# ---------- нормализация и псевдоним ----------

def test_normalize_drops_common_coefficient():
    expr = -2 * sp.Symbol("mu_0") * (div(sp.Symbol("j")) + ddt(sp.Symbol("rho")))
    assert normalize_zero_form(expr) == div(sp.Symbol("j")) + ddt(sp.Symbol("rho"))


def test_normalize_keeps_nonproportional():
    mu, j, rho = sp.Symbol("mu_0"), sp.Symbol("j"), sp.Symbol("rho")
    expr = mu * div(j) + 2 * mu * ddt(rho)
    assert normalize_zero_form(expr) == expr


def test_alias_ddt_symbol():
    assert apply_canon_alias(ddt(sp.Symbol("rho"))) == sp.Symbol("drho_dt")


def test_zero_form_matches_negative():
    expr, _ = derive_continuity()
    assert not zero_form_matches(expr, "div(j) + drho_dt + div(E)")
