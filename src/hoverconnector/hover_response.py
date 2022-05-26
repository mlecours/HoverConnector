from requests import Response
from requests.cookies import RequestsCookieJar


class HoverResponse:
    def __init__(self, response: Response, cookies: RequestsCookieJar = None) -> None:
        super().__init__()
        self.status_code = response.status_code
        self.cookies = cookies or response.cookies
        self.content = response.json() \
            if "json" in response.headers.get("Content-Type", "").lower() \
            else response.content
