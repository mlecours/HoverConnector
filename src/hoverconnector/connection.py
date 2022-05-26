import requests
from requests import Response
from requests.cookies import RequestsCookieJar

from hoverconnector.record_type import RecordType
from hoverconnector.exceptions import HoverLoginException, ConnectionConfigurationException
from hoverconnector.hover_response import HoverResponse


class Connection:
    def __init__(self, configuration: dict = None, cookies: RequestsCookieJar = None) -> None:
        super().__init__()
        if configuration is None:
            configuration = {}

        credential_config = configuration.get("credential", {})
        self.username = credential_config.get("username", None)
        self.password = credential_config.get("password", None)

        endpoints_config = configuration.get("endpoints", {})
        self.endpoints = dict(
            protocol=endpoints_config.get("protocol", "https"),
            base=endpoints_config.get("base", None),
            establish=endpoints_config.get("establish", None),
            login=endpoints_config.get("login", None),
            list_domains=endpoints_config.get("list_domains", None),
            list_entries=endpoints_config.get("list_entries", None),
            create_entry=endpoints_config.get("create_entry", None),
            update_entry=endpoints_config.get("update_entry", None)
        )

        self.cookies = cookies or RequestsCookieJar()

    def log_in(self, username: str = None, password: str = None, save=True,
               cookies: RequestsCookieJar = None) -> HoverResponse:
        cookies = cookies or self.cookies or RequestsCookieJar()
        username = username or self.username
        password = password or self.password

        cookies.clear_expired_cookies()

        # When an "hover_session" has not yet been established, we need to retrieve a page to get the "session" ID
        if len(cookies.items()) == 0 or "hover_session" not in cookies:
            response = requests.get(url=self.endpoint_establish())
        else:
            response = requests.get(url=self.endpoint_establish(), cookies=cookies, allow_redirects=False)
        cookies.update(response.cookies)
        self.update_cookies(cookies)

        if status_is(response.status_code, 200):
            required_fields = ["username", "password"]
            if username is not None:
                required_fields.remove("username")
            if password is not None:
                required_fields.remove("password")

            if required_fields:
                raise ConnectionConfigurationException(*required_fields)
            response = requests.post(url=self.endpoint_login(),
                                     json={"username": username, "password": password, "remember": save},
                                     cookies=cookies)

            if not status_is(response.status_code, 200):
                raise HoverLoginException(response=response)

            cookies.update(response.cookies)
            self.cookies.update(cookies)
        return HoverResponse(response=response, cookies=cookies)

    def update_cookies(self, cookies: RequestsCookieJar) -> None:
        self.cookies.update(cookies)

    def list_domains(self, cookies: RequestsCookieJar = None) -> Response:
        cookies = cookies or self.cookies
        return requests.get(self.endpoint_list_domains(), cookies=cookies)

    def get_domain(self, domain_name: str, cookies: RequestsCookieJar = None) -> Response:
        cookies = cookies or self.cookies
        return requests.get(self.endpoint_domain(domain_name), cookies=cookies)

    def update_entry(self, domain_name: str, dns_entry_id: str, name: str, record_type: RecordType = RecordType.A,
                     content: str = None, ttl: int = None, cookies: RequestsCookieJar = None) -> Response:
        cookies = cookies or self.cookies
        json_payload = {
            "domain": {
                "id": f"domain-{domain_name}",
                "dns_records": [{
                    "id": dns_entry_id,
                    "name": name,
                    "type": record_type.value
                }],
            },
            "fields": {
            }
        }
        if content is not None and len(content) > 0:
            json_payload["fields"]["content"] = content
        if ttl is not None and ttl > 0:
            json_payload["fields"]["ttl"] = ttl

        return requests.put(self.endpoint_update_entry(), cookies=cookies, json=json_payload)

    def create_entry(self, domain_name: str, name: str, record_type: RecordType, content: str, ttl: int,
                     cookies: RequestsCookieJar = None) -> Response:
        cookies = cookies or self.cookies

        json_payload = {
            "dns_record": {
                "name": name,
                "content": content,
                "type": record_type.value,
                "ttl": ttl
            },
            "id": f"domain-{domain_name}"
        }
        return requests.post(self.endpoint_create_entry(), cookies=cookies, json=json_payload)

    def create_mx_entry(self, domain_name: str, mail_server: str, name: str = "@", priority: int = 0, ttl: int = 300,
                        cookies: RequestsCookieJar = None) -> Response:
        return self.create_entry(
            record_type=RecordType.MX,
            domain_name=domain_name, name=name, content=f'{priority} {mail_server}', ttl=ttl, cookies=cookies,
        )

    def endpoint_establish(self) -> str:
        endpoint = self.endpoints["establish"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.establish")

        return f'{self.endpoint_base()}{endpoint}'

    def endpoint_login(self) -> str:
        endpoint = self.endpoints["login"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.login")

        return f'{self.endpoint_base()}{endpoint}'

    def endpoint_list_domains(self) -> str:
        endpoint = self.endpoints["list_domains"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.list_domains")

        return f'{self.endpoint_base()}{endpoint}'

    def endpoint_domain(self, domain_name: str) -> str:
        endpoint = self.endpoints["list_entries"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.list_entries")

        return f'{self.endpoint_base()}{endpoint}'.replace('{domain}', domain_name)

    def endpoint_update_entry(self) -> str:
        endpoint = self.endpoints["update_entry"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.update_entry")

        return f'{self.endpoint_base()}{endpoint}'

    def endpoint_create_entry(self) -> str:
        endpoint = self.endpoints["create_entry"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.create_entry")

        return f'{self.endpoint_base()}{endpoint}'

    def endpoint_base(self) -> str:
        endpoint = self.endpoints["base"]
        if endpoint is None:
            raise ConnectionConfigurationException("endpoints.base")

        return f'{self.endpoints["protocol"]}://{endpoint}'


def status_is(status_code, range_start):
    return range_start <= status_code < range_start + 100
