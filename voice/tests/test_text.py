import pytest

from voice.profiles import CategoryError, get_category, list_categories, resolve_category
from voice.text import detect_script, normalize_text, split_segments, tokenize


def test_detect_script():
    assert detect_script("Салом дунё") == "cyrillic"
    assert detect_script("Salom dunyo") == "latin"


def test_latin_to_cyrillic_transliteration():
    result = normalize_text("Assalomu alaykum!", language="auto")
    assert "ассалому" in result
    assert "алайкум" in result
    assert "!" not in result


def test_uzbek_specific_letters():
    result = normalize_text("O'zbek tili, g'isht qanday?", language="auto")
    assert "ўзбек" in result
    assert "ғишт" in result
    assert "қандай" in result


def test_digits_expanded():
    result = normalize_text("Salom 7", language="auto")
    assert "етти" in result
    assert "7" not in result


def test_tokenizer_matches_model_vocab():
    tokenizer_path = "voice/models/male/tokenizer.json"
    ids = tokenize("Салом", tokenizer_path, language="cyrillic")
    assert ids and all(0 <= value <= 45 for value in ids)
    assert ids[0] == 0 and ids[-1] == 0
    assert len(ids) == 2 * len(normalize_text("Салом", language="cyrillic")) + 1


def test_empty_text_returns_no_tokens():
    assert tokenize("!!!", "voice/models/male/tokenizer.json", language="cyrillic") == []


def test_split_segments_respects_limit():
    text = "Биринчи гап. Иккинчи гап. Учинчи гап."
    segments = split_segments(text, max_chars=15)
    assert len(segments) >= 2
    assert all(len(part) <= 15 for part in segments)


def test_categories_and_aliases():
    names = {item["id"] for item in list_categories()}
    assert {"male", "female", "boy", "girl", "child", "elderly"} <= names
    assert resolve_category("qiz") == "girl"
    assert resolve_category("bola") == "child"
    assert get_category("erkak")[0] == "male"
    with pytest.raises(CategoryError):
        get_category("unknown_voice")
