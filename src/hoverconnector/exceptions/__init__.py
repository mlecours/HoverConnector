from requests import Response


class ConnectionConfigurationException(Exception):
    def __init__(self, *args) -> None:
        super().__init__(f"Missing configuration items: {', '.join(args)}")


class HoverLoginException(Exception):
    def __init__(self, response: Response) -> None:
        super().__init__(response.content.decode(response.encoding), response.status_code)
