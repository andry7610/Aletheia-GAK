
# test/test_seed_db.py
import math
from seed_db import CODATA_VALUES, CONSTANTS, verify_codata_consistency


def _constant_names():
    # Достаём имена констант независимо от структуры справочника
    return {entry[0] for entry in CONSTANTS}


def test_all_constants_present():
    expected = {"c", "G", "h", "hbar", "k_B", "e", "m_e", "m_p",
                "epsilon_0", "mu_0", "N_A", "R", "sigma_SB"}
    assert expected == _constant_names()


def test_codata_values_complete():
    assert set(CODATA_VALUES) == _constant_names()
    assert all(isinstance(v, float) and v > 0 for v in CODATA_VALUES.values())


def test_exact_speed_of_light():
    assert CODATA_VALUES["c"] == 299792458.0


def test_hbar_consistency():
    # hbar выводится из h, тождество должно сходиться до 1e-15
    assert math.isclose(CODATA_VALUES["hbar"] * 2 * math.pi,
                        CODATA_VALUES["h"], rel_tol=1e-15)


def test_R_equals_NA_kB():
    assert math.isclose(CODATA_VALUES["R"],
                        CODATA_VALUES["N_A"] * CODATA_VALUES["k_B"], rel_tol=1e-15)


def test_sigma_SB_consistency():
    k_B, hbar, c = CODATA_VALUES["k_B"], CODATA_VALUES["hbar"], CODATA_VALUES["c"]
    expected = math.pi ** 2 * k_B ** 4 / (60 * hbar ** 3 * c ** 2)
    assert math.isclose(CODATA_VALUES["sigma_SB"], expected, rel_tol=1e-12)


def test_verify_function_runs():
    assert verify_codata_consistency() is True
