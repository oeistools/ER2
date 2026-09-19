"""``er2.oeis`` against oeis.org; run with ``ER2_NETWORK_TESTS=1``."""

import os

import pytest

from er2 import oeis, prelude

pytestmark = pytest.mark.skipif(
    not os.environ.get("ER2_NETWORK_TESTS"),
    reason="network test (set ER2_NETWORK_TESTS=1)",
)


def test_live_lookup_identify_and_check():
    assert oeis.sequence("A000045")[10] == 55
    sigma = prelude.namespace()["sigma"]
    assert oeis.identify(sigma, 20)[0].id == "A000203"
    assert oeis.check(sigma, "A000203", count=200)
