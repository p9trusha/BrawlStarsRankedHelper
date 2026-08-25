import pytest

from brawlstars_api import normalize_tag


class TestNormalizeTag:
    def test_strips_hash_and_spaces(self):
        assert normalize_tag("#2PR8J29GL") == "2PR8J29GL"

    def test_uppercases(self):
        assert normalize_tag("2pr8j29gl") == "2PR8J29GL"

    def test_inner_spaces_removed(self):
        assert normalize_tag("2P R8 J2") == "2PR8J2"

    def test_valid_alphabet(self):
        assert normalize_tag("0289PYLQGRJC") == "0289PYLQGRJC"

    def test_empty_raises(self):
        with pytest.raises(RuntimeError):
            normalize_tag("   ")

    def test_hash_only_raises(self):
        with pytest.raises(RuntimeError):
            normalize_tag("#")

    def test_too_short_raises(self):
        with pytest.raises(RuntimeError):
            normalize_tag("AB")

    def test_too_long_raises(self):
        with pytest.raises(RuntimeError):
            normalize_tag("A" * 13)

    @pytest.mark.parametrize("bad", ["АБВ", "2PR<", "2PR>", "2PR&", "2PR1"])
    def test_invalid_characters_raise(self, bad):
        with pytest.raises(RuntimeError):
            normalize_tag(bad)
