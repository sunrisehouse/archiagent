from archiagent.model.base import ModelClient
from archiagent.model.fake import FakeModel

__all__ = ["ModelClient", "FakeModel", "get_default_model"]


def get_default_model():
    """자격이 있으면 실제 Claude 모델, 없으면 None 을 돌려준다.

    실모델은 무거운 import 를 피하려 지연 로딩한다. 자격(구독 OAuth 또는 API 키)이
    없으면 None — 호출 측이 FakeModel 로 폴백한다.
    """
    from archiagent.model.claude import ClaudeModel

    return ClaudeModel.if_available()
