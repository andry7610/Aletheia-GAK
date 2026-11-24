import ast
import operator
import pint


class AletheiaVerifier:
    def __init__(self):
        self.ureg = pint.UnitRegistry()
        if "electron_volt" not in self.ureg:
            self.ureg.define("electron_volt = 1.602176634e-19 joule = eV")
        self._bin_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
        }
        self._unary_ops = {
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }
        self._dimensionless_funcs = {
            "exp", "log", "ln", "log10", "sin", "cos", "tan", "expit"
        }
        self._allowed_modules = {"math", "np", "numpy", "sp", "scipy", "special"}
        self._builtin_constants = {
            "pi": self.ureg.Quantity(3.141592653589793, "dimensionless"),
            "e": self.ureg.Quantity(2.718281828459045, "dimensionless"),
            "tau": self.ureg.Quantity(6.283185307179586, "dimensionless"),
        }

    def _get_attr_chain(self, node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.Attribute):
            return self._get_attr_chain(node.value) + [node.attr]
        raise ValueError("Неподдерживаемый вызов функции")

    def _eval_ast(self, node: ast.AST, env: dict[str, pint.Quantity]):
        if isinstance(node, ast.Expression):
            return self._eval_ast(node.body, env)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return self.ureg.Quantity(node.value, "dimensionless")
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise ValueError(f"Неизвестная переменная: '{node.id}'")
            return env[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._unary_ops:
            return self._unary_ops[type(node.op)](self._eval_ast(node.operand, env))
        if isinstance(node, ast.BinOp) and type(node.op) in self._bin_ops:
            left = self._eval_ast(node.left, env)
            right = self._eval_ast(node.right, env)
            if isinstance(node.op, ast.Pow):
                if not right.dimensionless:
                    raise pint.DimensionalityError(
                        right.units, "dimensionless",
                        extra_msg="Показатель степени должен быть безразмерным"
                    )
                return left ** right.magnitude
            return self._bin_ops[type(node.op)](left, right)
        if isinstance(node, ast.Call):
            chain = self._get_attr_chain(node.func)
            fname = chain[-1]
            if len(chain) > 1 and not set(chain[:-1]).issubset(self._allowed_modules):
                raise ValueError(f"Запрещённый модуль в вызове: '{'.'.join(chain)}'")
            if len(node.args) != 1:
                raise ValueError(f"Функция '{fname}' должна принимать 1 аргумент")
            arg = self._eval_ast(node.args[0], env)
            if fname in self._dimensionless_funcs:
                if not arg.dimensionless:
                    raise pint.DimensionalityError(
                        arg.units, "dimensionless",
                        extra_msg=f"Аргумент {fname}() обязан быть безразмерным!"
                    )
                return self.ureg.Quantity(1.0, "dimensionless")
            if fname == "sqrt":
                return arg ** 0.5
            raise ValueError(f"Запрещённая или неизвестная функция: '{fname}'")
        raise ValueError(f"Неподдерживаемая конструкция AST: {ast.dump(node)}")

    def verify_equation(
        self, equation_str: str, symbols: dict[str, str]
    ) -> tuple[bool, str]:
        """
        Проверяет уравнение вида 'lhs = rhs' с картой размерностей symbols.
        """
        if "=" not in equation_str:
            return False, "ОШИБКА формата: уравнение должно содержать знак '='"
        lhs_str, rhs_str = [part.strip() for part in equation_str.split("=", 1)]
        lhs_str = lhs_str.replace("^", "**")
        rhs_str = rhs_str.replace("^", "**")

        try:
            env = dict(self._builtin_constants)
            for name, unit_str in symbols.items():
                env[name] = self.ureg.Quantity(1.0, unit_str)
            lhs_q = self._eval_ast(ast.parse(lhs_str, mode="eval"), env)
            rhs_q = self._eval_ast(ast.parse(rhs_str, mode="eval"), env)

            if lhs_q.dimensionality == rhs_q.dimensionality:
                return True, f"OK: {lhs_q.dimensionality}"
            return (
                False,
                f"ОШИБКА размерности: левая часть [{lhs_q.dimensionality}] != правая [{rhs_q.dimensionality}]",
            )
        except pint.errors.DimensionalityError as e:
            return False, f"ОШИБКА размерности: {e}"
        except Exception as e:
            return False, f"ОШИБКА проверки: {e}"
