import os

import pytest

from voice.profiles import CategoryError, get_category, list_categories, resolve_category
from voice.text import detect_script, normalize_text, split_segments, tokenize

# Model fayllari repo ildiziga nisbatan. Nisbiy yo'l CWD'ga bog'liq bo'lib
# qolardi: testlar `conduit/voice` dan yurgizilganda `voice/models/...`
# topilmasdi (FileNotFoundError) — ya'ni faqat repo ildizidan ishlardi.
_MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_TOKENIZER = os.path.join(_MODELS, "male", "tokenizer.json")


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
    tokenizer_path = _TOKENIZER
    ids = tokenize("Салом", tokenizer_path, language="cyrillic")
    assert ids and all(0 <= value <= 45 for value in ids)
    assert ids[0] == 0 and ids[-1] == 0
    assert len(ids) == 2 * len(normalize_text("Салом", language="cyrillic")) + 1


def test_empty_text_returns_no_tokens():
    assert tokenize("!!!", _TOKENIZER, language="cyrillic") == []


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


# --- Regressiya: `uz` tili va token id chegarasi (2026-11-27) ---
# Ildiz sabab 1: normalize_text `uz` ni tanilmagan qiymat deb o'tkazib
# yuborardi -> lotin harflar lug'atda yo'q -> unk id 45 (lug'at 0..44).
# Ildiz sabab 2: tokenize'da `vocab.get("<unk>", 45)` chegaradan chiqadigan
# zaxira id berardi. ONNX Runtime "indices element out of data bounds" beradi.

import json
from pathlib import Path

import pytest as _pytest

_VOCAB_PATH = Path(__file__).resolve().parents[1] / "models" / "male" / "tokenizer.json"


def _vocab():
    return json.loads(_VOCAB_PATH.read_text(encoding="utf-8"))["model"]["vocab"]


@_pytest.mark.parametrize("language", ["uz", "uzbek", "auto", "latin"])
def test_uz_language_produces_cyrillic(language):
    """`uz` ham lotin matnni Kirillga o'girishi shart."""
    result = normalize_text("Salom dunyo", language=language)
    assert result, f"{language}: natija bo'sh"
    assert not any(c.isascii() and c.isalpha() for c in result), (
        f"{language}: lotin harflari qoldi -> {result!r}"
    )


@_pytest.mark.parametrize("language", ["uz", "auto", "latin", "cyrillic"])
@pytest.mark.parametrize("text", ["Salom dunyo", "Привет мир", "Цена 5", "test-text", "O'zbek g'isht"])
def test_token_ids_never_exceed_vocab(language, text):
    """Har qanday rejimda token id lug'at chegarasida bo'lishi shart."""
    vocab = _vocab()
    max_id = max(vocab.values())
    ids = tokenize(text, _VOCAB_PATH, language=language)
    assert ids, f"{language}/{text}: token bo'sh"
    bad = [i for i in ids if not (0 <= i <= max_id)]
    assert not bad, f"{language}/{text}: chegaradan chiqqan id {bad} (max {max_id})"


def test_tokenize_falls_back_to_valid_id_not_45():
    """`<unk>` lug'atda bo'lmasa ham zaxira id lug'at ichida bo'lishi shart."""
    vocab = _vocab()
    assert "<unk>" not in vocab, "test fixture o'zgargan — bu model <unk> bermaydi"
    max_id = max(vocab.values())
    ids = tokenize("abc", _VOCAB_PATH, language="uz")
    assert max(ids) <= max_id
