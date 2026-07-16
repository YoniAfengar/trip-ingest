"""The size gate: every function in src/ <= 20 code lines, every file <= 250."""
from check_loc import find_violations


def test_src_is_small():
    violations = find_violations(["src"])
    assert not violations, "\n".join(violations)
