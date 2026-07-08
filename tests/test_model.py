"""_extract_json — 실모델 출력에서 첫 JSON 객체를 안전하게 뽑는지 검증(모델 호출 없음)."""

import pytest

from archiagent.model.claude import _extract_json


def test_plain_json():
    assert _extract_json('{"relevant": true, "reason": "x"}') == {"relevant": True, "reason": "x"}


def test_code_fenced_json():
    out = "설명입니다.\n```json\n{\"title\": \"설계서\"}\n```\n끝."
    assert _extract_json(out) == {"title": "설계서"}


def test_braces_inside_string_value():
    # 본문 문자열에 { } 가 들어가도 깨지지 않아야 한다(과거 중괄호 세기 버그).
    out = '{"title": "설계서", "body": "설정은 env {ENV} 로 주입한다. 예: config {a:1}", "addresses": ["R-1"]}'
    got = _extract_json(out)
    assert got["addresses"] == ["R-1"]
    assert "{ENV}" in got["body"]


def test_trailing_text_after_json():
    assert _extract_json('{"relevant": false} 이후 설명 텍스트') == {"relevant": False}


def test_no_json_raises():
    with pytest.raises(ValueError):
        _extract_json("여기에는 JSON 이 없습니다.")
