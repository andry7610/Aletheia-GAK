import sqlite3
import sympy as sp


class AletheiaMemory:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

        # Канонические связи констант
        self.relations = {
            sp.Symbol("hbar"): sp.Symbol("h") / (2 * sp.pi),
            # Кулоновская постоянная: k_e = 1 / (4 * pi * epsilon_0)
            sp.Symbol("k_e"): 1 / (4 * sp.pi * sp.Symbol("epsilon_0"))
        }

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quantities (
                name TEXT PRIMARY KEY,
                dimension TEXT,
                description TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS laws (
                name TEXT PRIMARY KEY,
                lhs TEXT,
                rhs TEXT
            )
            """
        )
        self.conn.commit()

    def add_quantity(self, name: str, dimension: str, description: str = ""):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO quantities (name, dimension, description) VALUES (?, ?, ?)",
            (name, dimension, description),
        )
        self.conn.commit()

    def add_law(self, name: str, lhs_str: str, rhs_str: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO laws (name, lhs, rhs) VALUES (?, ?, ?)",
            (name, lhs_str, rhs_str),
        )
        self.conn.commit()

    def close(self):
        """Закрывает соединение с SQLite (вызывается в конце populate_knowledge_base)."""
        self.conn.close()

    def get_symbols_dict(self) -> dict[str, str]:
        """Возвращает словарь известных размерностей для AletheiaVerifier."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, dimension FROM quantities")
        return {row["name"]: row["dimension"] for row in cursor.fetchall()}

    def _safe_parse(self, expr_str: str, safe_locals: dict) -> sp.Expr:
        if "__" in expr_str:
            raise ValueError("Запрещённые символы '__' во входном выражении")
        safe_globals = {
            "Integer": sp.Integer,
            "Float": sp.Float,
            "Rational": sp.Rational,
            # Фикс Алечки: без Symbol парсер падал с NameError на любых
            # именах вне базы вместо нормального фидбека
            "Symbol": sp.Symbol,
        }
        expr = sp.parse_expr(
            expr_str.replace("^", "**"),
            local_dict=safe_locals,
            global_dict=safe_globals,
        )
        # Неизвестные символы отсекаем явно, а не "молча создаём"
        unknown = sorted(s.name for s in expr.free_symbols if s.name not in safe_locals)
        if unknown:
            raise ValueError(
                "неизвестные символы: " + ", ".join(unknown)
                + " — добавьте их через add_quantity()"
            )
        return expr

    def check_algebraic_law(
        self, proposed_lhs_str: str, proposed_rhs_str: str, law_name: str
    ) -> tuple[bool, str]:
        """Безопасная алгебраическая сверка формулы с каноническим законом."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT lhs, rhs FROM laws WHERE name = ?", (law_name,))
        row = cursor.fetchone()
        if not row:
            return False, f"Закон '{law_name}' не найден в Гиппокампе."

        # Собираем белый список символов прямо из базы знаний + базовые мат. функции
        safe_locals = {
            name: sp.Symbol(name) for name in self.get_symbols_dict().keys()
        }
        safe_locals.update({
            "pi": sp.pi,
            "exp": sp.exp,
            "log": sp.log,
            "sin": sp.sin,
            "cos": sp.cos,
            "sqrt": sp.sqrt,
        })

        try:
            canonical_lhs = self._safe_parse(row["lhs"], safe_locals).subs(self.relations)
            canonical_rhs = self._safe_parse(row["rhs"], safe_locals).subs(self.relations)

            proposed_lhs = self._safe_parse(proposed_lhs_str, safe_locals).subs(self.relations)
            proposed_rhs = self._safe_parse(proposed_rhs_str, safe_locals).subs(self.relations)
        except Exception as e:
            return False, f"Ошибка безопасного парсинга SymPy: {e}"

        prop = sp.together(proposed_lhs - proposed_rhs)
        canon = sp.together(canonical_lhs - canonical_rhs)

        # Каскад Алечки: сверка тождества ЦЕЛЫХ уравнений,
        # а не их частей (инвариантно к перевороту и переносу слагаемых)
        #
        # Примечание (Шаг 2): каноны с нулевой правой частью (законы сохранения)
        # обрабатываются тем же каскадом: разница канона div_J + drho_dt - 0
        # ненулевая, поэтому срабатывает шаг пропорциональности.

        # Шаг 1: прямое тождество
        residual = sp.simplify(sp.cancel(prop - canon))
        if residual.equals(0):
            return True, f"OK: совпадает с каноническим законом '{law_name}'."

        # Шаг 2: пропорциональность с точностью до ненулевой константы
        # (ловит 0 = 2*J против 0 = J)
        if canon != 0:
            k = sp.simplify(sp.cancel(prop / canon))
            if k.is_number and k != 0:
                if sp.simplify(prop - k * canon).equals(0):
                    return True, (
                        f"OK: эквивалентно канону '{law_name}' "
                        f"с точностью до множителя {k}."
                    )

        # Шаг 3: эквивалентность нулевых множеств
        # (ловит умножение уравнения на переменный множитель: m = E/c^2)
        shared = sorted(prop.free_symbols & canon.free_symbols, key=lambda s: s.name)
        for s in shared:
            sol_prop = [sp.simplify(x) for x in sp.solve(prop, s)]
            sol_canon = [sp.simplify(x) for x in sp.solve(canon, s)]
            if len(sol_prop) == len(sol_canon) and all(
                any(a.equals(b) for b in sol_canon) for a in sol_prop
            ):
                return True, (
                    f"OK: эквивалентно канону '{law_name}' "
                    f"(умножение на переменный множитель)."
                )

        return (
            False,
            f"ОШИБКА: физика не сходится с '{law_name}'. "
            f"Разница: {proposed_lhs} - {proposed_rhs} vs "
            f"{canonical_lhs} - {canonical_rhs}. Проверьте константы.",
        )
