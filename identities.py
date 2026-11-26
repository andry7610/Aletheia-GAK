# -*- coding: utf-8 -*-
"""
identities — слой тождеств векторного анализа для Aletheia-GAK (v1.2).

Отдельный слой правил упрощения, НЕ смешанный с физическими законами:
  - тождества (identities) истинны всегда, для любых полей;
  - законы (laws) живут в Гиппокампе и сверяются каскадом отдельно.

Реализованные нулевые тождества:
  div(rot(A))    = 0   (включая псевдоним curl)
  rot(grad(phi)) = 0

Негативные случаи НЕ трогаются (иначе мы бы тихо ломали физику):
  div(grad(phi)) — это лапласиан, не ноль;
  rot(rot(B))    — это rot rot B, не ноль.

Скалярный множитель не мешает сворачиванию: div(k*rot(A)) = k*div(rot(A)) = 0.
Ограничение безопасности: сворачиваем только если все прочие множители — числа,
чтобы не маскировать ошибки рангов (произведения полей рубит RankChecker).

Конвейер оркестратора: AST -> тождества -> ранги/единицы -> размерности -> каскад.
"""
from typing import Dict, Optional, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from vector_ops import (
    RankChecker, AletheiaTypeError, Inferred,
    grad, div, rot, curl, ddt,
)

__all__ = ["simplify_identities", "IdentitySimplifier", "ZERO_IDENTITIES"]

# распознавание операторов — отдельно от таблицы тождеств
_OP_ALIASES = {"curl": "rot"}
OP_NAMES = {"grad", "div", "rot", "ddt"}

# канонические имена (внешний, внутренний) -> нулевое тождество
ZERO_IDENTITIES = {("div", "rot"), ("rot", "grad")}


def _op_name(func) -> Optional[str]:
    """Каноническое имя оператора или None, если это не оператор."""
    name = func.__name__
    if name in _OP_ALIASES:
        name = _OP_ALIASES[name]
    return name if name in OP_NAMES else None


def _is_zero_pattern(expr: sp.Expr) -> bool:
    """Является ли узел сворачиваемым нулевым тождеством.

    Поддерживает скалярный множитель: div(k*rot(A)) -> k*div(rot(A)) = 0.
    Прочие множители должны быть числами, чтобы не маскировать
    ошибки рангов — их ловит RankChecker на следующем проходе.
    """
    if not isinstance(expr, sp.core.function.AppliedUndef):
        return False
    if len(expr.args) != 1:
        return False
    outer = _op_name(expr.func)
    if outer is None:
        return False

    arg = expr.args[0]
    op_nodes = []
    other_factors = []

    if isinstance(arg, sp.core.function.AppliedUndef):
        op_nodes.append(arg)
    elif isinstance(arg, sp.Mul):
        for factor in sp.Mul.make_args(arg):
            if isinstance(factor, sp.core.function.AppliedUndef) \
                    and _op_name(factor.func) is not None:
                op_nodes.append(factor)
            else:
                other_factors.append(factor)
    else:
        return False

    if len(op_nodes) != 1:
        return False
    inner_node = op_nodes[0]
    if not (isinstance(inner_node, sp.core.function.AppliedUndef)
            and len(inner_node.args) == 1):
        return False
    inner = _op_name(inner_node.func)
    if inner is None or (outer, inner) not in ZERO_IDENTITIES:
        return False

    return all(f.is_number for f in other_factors)


def _simplify_node(expr: sp.Expr) -> sp.Expr:
    if isinstance(expr, sp.Add):
        kept = [_simplify_node(a) for a in expr.args]
        kept = [a for a in kept if not a.is_zero]
        if not kept:
            return sp.S.Zero
        return sp.Add(*kept) if len(kept) > 1 else kept[0]

    if isinstance(expr, sp.Mul):
        factors = [_simplify_node(f) for f in sp.Mul.make_args(expr)]
        if any(f.is_zero for f in factors):
            return sp.S.Zero
        return sp.Mul(*factors)

    if isinstance(expr, sp.core.function.AppliedUndef):
        rebuilt = expr.func(*[_simplify_node(a) for a in expr.args])
        if _is_zero_pattern(rebuilt):
            return sp.S.Zero
        return rebuilt

    return expr


def simplify_identities(expr: sp.Expr) -> sp.Expr:
    """Схлопывает нулевые тождества векторного анализа, остальное не трогает."""
    if not isinstance(expr, sp.Basic):
        raise AletheiaTypeError("simplify_identities принимает SymPy-выражение")
    return _simplify_node(expr)


class IdentitySimplifier:
    """Обёртка над слоем тождеств с мини-конвейером для оркестратора."""

    def __init__(self, registry: Dict[str, "SymbolInfo"] = None):
        self.rank_checker = RankChecker(registry)

    def simplify_text(self, text: str) -> sp.Expr:
        return simplify_identities(self._parse(text))

    def check_text(self, text: str) -> Tuple["Inferred", sp.Expr]:
        expr = self.simplify_text(text)
        return self.rank_checker.check(expr), expr

    def _parse(self, text: str) -> sp.Expr:
        if "__" in text:
            raise AletheiaTypeError("Запрещённые символы '__' во входном выражении")
        safe_globals = {
            "Integer": sp.Integer,
            "Float": sp.Float,
            "Rational": sp.Rational,
            "Symbol": sp.Symbol,
            "Function": sp.Function,
        }
        local = {name: sp.Symbol(name) for name in self.rank_checker.registry}
        local.update({"grad": grad, "div": div, "rot": rot,
                      "curl": rot, "ddt": ddt})
        try:
            return parse_expr(text, local_dict=local, global_dict=safe_globals)
        except Exception as e:
            raise AletheiaTypeError(f"Не удалось разобрать выражение: {e}") from e
