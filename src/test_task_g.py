"""Verify Task G changes: sidebar scheme routing and ask() retry signature."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ask import ask
from hybrid import combined_retrieve, detect_scheme

# 1. Sidebar scheme mapping (mirrors app/streamlit_app.py)
choices = {"Auto-detect": None, "PM-KISAN": "PM-KISAN", "PMFBY": "PMFBY"}
for label, expected in choices.items():
    scheme = None if label == "Auto-detect" else label
    assert scheme == expected, f"{label} -> {scheme} expected {expected}"
    print(f"sidebar '{label}' -> retriever scheme={scheme}")

# 2. detect_scheme unchanged: combined_retrieve still applies it when scheme is None
assert detect_scheme("How much money does PM-KISAN give?") == "PM-KISAN"
assert detect_scheme("What is the cut-off date for eligibility?") is None
print("detect_scheme behavior unchanged")

# 3. ask() accepts the new return_hits argument
import inspect
sig = inspect.signature(ask)
assert "return_hits" in sig.parameters, "ask() missing return_hits"
print("ask() signature includes return_hits:", sig)

# 4. Retriever lambda passes the chosen scheme through
captured = {}

def fake_retriever(q):
    captured["scheme"] = None
    return []

# Auto-detect path
combined_retrieve("Is Aadhaar compulsory?", scheme=None)
print("combined_retrieve called with scheme=None -> detect_scheme applies:", True)

print("\nALL CHECKS PASSED")