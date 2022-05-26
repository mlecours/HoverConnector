from typing import Any

from hamcrest import has_entry, has_entries
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description
from hamcrest.core.matcher import Matcher
from requests import Response

from hoverconnector.connection import Connection


class ResponseStatusCodeMatcher(BaseMatcher):
    def __init__(self, status_code: int) -> None:
        super().__init__()
        self.status_code = status_code

    def _matches(self, item: Response) -> bool:
        return self.status_code == item.status_code

    def describe_to(self, description: Description) -> None:
        description.append_description_of(f"response status code is {self.status_code}")

    def describe_mismatch(self, item: Response, mismatch_description: Description) -> None:
        super().describe_mismatch(f"{item.status_code} - {item.json()}", mismatch_description)


class ResponseContentMatcher(BaseMatcher):
    def __init__(self, content: Any) -> None:
        super().__init__()
        self.content = content

    def _matches(self, item: Response) -> bool:
        return self.content == item.content

    def describe_to(self, description: Description) -> None:
        description.append_description_of(f"response content is: {self.content}")

    def describe_mismatch(self, item: Response, mismatch_description: Description) -> None:
        super().describe_mismatch(f"{item.content}", mismatch_description)


class ResponseJsonContentMatcher(BaseMatcher):
    def __init__(self, content) -> None:
        super().__init__()
        self.matcher = has_entries(content)

    def _matches(self, item: Response) -> bool:
        return self.matcher.matches(item.json())

    def describe_to(self, description: Description) -> None:  # pragma: no cover
        description.append_description_of(f"response JSON content is: {self.matcher}")

    def describe_mismatch(self, item: Response, mismatch_description: Description) -> None:
        super().describe_mismatch(item.json() if item.json() else item, mismatch_description)


class ConnectionMatcher(BaseMatcher):
    def __init__(self, property_name: str, matcher: Matcher) -> None:
        super().__init__()
        self.property_name = property_name
        self.matcher = matcher

    def _matches(self, item: Connection) -> bool:
        return self.property_name in item.__dict__ and \
               self.matcher.matches(item.__getattribute__(self.property_name))

    def describe_to(self, description: Description) -> None:
        description.append_text(f"{self.property_name} is ")
        self.matcher.describe_to(description)

    def describe_mismatch(self, item: Response, mismatch_description: Description) -> None:
        super().describe_mismatch(item.__getattribute__(self.property_name), mismatch_description)


def has_username(matcher: Matcher):
    return ConnectionMatcher(property_name="username", matcher=matcher)


def has_password(matcher: Matcher):
    return ConnectionMatcher(property_name="password", matcher=matcher)


def has_endpoint(endpoint: str, matcher: Matcher):
    return ConnectionMatcher(property_name="endpoints", matcher=has_entry(endpoint, matcher))


def has_protocol(matcher: Matcher):
    return has_endpoint("protocol", matcher)


def has_base(matcher: Matcher):
    return has_endpoint("base", matcher)


def has_status_code(status_code: int):
    return ResponseStatusCodeMatcher(status_code=status_code)


def has_json_content(content: dict):
    return ResponseJsonContentMatcher(content=content)
