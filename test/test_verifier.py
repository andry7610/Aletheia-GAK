import pytest
from verifier import AletheiaVerifier

@pytest.fixture
def verifier():
    return AletheiaVerifier()

def test_boltzmann_pass(verifier):
    eq = "P = P0 * np.exp(-E / (k * T))"
    syms = {"P": "Pa", "P0": "Pa", "E": "J", "k": "J/K", "T": "K"}
    ok, msg = verifier.verify_equation(eq, syms)
    assert ok, f"Expected PASS, got {msg}"

def test_forgotten_gravity_fail(verifier):
    eq = "F = m * a + g"
    syms = {"F": "N", "m": "kg", "a": "m/s^2", "g": "m/s^2"}
    ok, msg = verifier.verify_equation(eq, syms)
    assert not ok, "Expected FAIL due to adding Newton and acceleration"

def test_entropy_in_sin_fail(verifier):
    eq = "Signal = A * math.sin(omega * t + S)"
    syms = {"Signal": "V", "A": "V", "omega": "1/s", "t": "s", "S": "J/K"}
    ok, msg = verifier.verify_equation(eq, syms)
    assert not ok, "Expected FAIL inside sin()"

def test_magnetic_confusion_fail(verifier):
    eq = "F = q * v * H"
    syms = {"F": "N", "q": "C", "v": "m/s", "H": "A/m"}
    ok, msg = verifier.verify_equation(eq, syms)
    assert not ok, "Expected FAIL because B != H dimensions"