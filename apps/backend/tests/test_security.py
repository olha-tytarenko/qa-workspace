from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

# A non-BMP character (an emoji, U+1F600) so backend/frontend password-length
# handling can be proven consistent: Python's `len()` counts it as one code
# point, while JS's `.length` would count it as two UTF-16 code units.
NON_BMP_PASSWORD = "correct-horse-battery" + "\U0001f600"


def test_hash_password_produces_an_argon2id_hash() -> None:
    hashed = hash_password("a sufficiently long password")

    assert hashed.startswith("$argon2id$")
    assert hashed != "a sufficiently long password"


def test_verify_password_accepts_the_matching_password() -> None:
    hashed = hash_password("a sufficiently long password")

    assert verify_password("a sufficiently long password", hashed) is True


def test_verify_password_rejects_a_different_password() -> None:
    hashed = hash_password("a sufficiently long password")

    assert verify_password("a different password entirely", hashed) is False


def test_hash_and_verify_round_trip_a_password_with_a_non_bmp_character() -> None:
    hashed = hash_password(NON_BMP_PASSWORD)

    assert verify_password(NON_BMP_PASSWORD, hashed) is True
    assert len(NON_BMP_PASSWORD) == 22  # Python counts the emoji as one code point.


def test_generate_session_token_produces_distinct_high_entropy_tokens() -> None:
    tokens = {generate_session_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(token) >= 40 for token in tokens)  # token_urlsafe(32) ~= 43 chars


def test_hash_session_token_is_a_deterministic_sha256_hex_digest() -> None:
    token = generate_session_token()

    first = hash_session_token(token)
    second = hash_session_token(token)

    assert first == second
    assert first != token
    assert len(first) == 64
    assert all(character in "0123456789abcdef" for character in first)
