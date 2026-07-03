"""Tests for __lib/stop_payload_schema factories."""

import pytest

from __lib.stop_payload_schema import make_stop_payload


class TestStopPayloadSchema:
    def test_make_stop_payload_rejects_unknown_keys(self):
        with pytest.raises(ValueError) as exc_info:
            make_stop_payload("t.jsonl", bogus_key=1)
        assert "bogus_key" in str(exc_info.value)
