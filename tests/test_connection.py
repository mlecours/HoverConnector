from unittest import TestCase

import yaml
from hamcrest import assert_that, equal_to, calling, raises, all_of, none, anything, has_entries
from httmock import HTTMock
from requests.cookies import RequestsCookieJar

from hoverconnector.connection import Connection
from hoverconnector.exceptions import ConnectionConfigurationException, HoverLoginException
from hoverconnector.record_type import RecordType
from testkit.hover_mock import http_mock_signin, http_mock_domains, http_mock_entry_update, http_mock_domain, \
    http_mock_entry_create
from testkit.matchers import has_status_code, has_username, has_password, has_protocol, has_base, has_endpoint, \
    has_json_content

test_config = """
        credential:
            username: my_username
            password: my_password
        endpoints:
            protocol: http
            base: fake_hover.local
            establish: /signin
            login: /signin/auth.json
            list_domains: /api/control_panel/domains
            list_entries: /api/control_panel/{domain}/dns
            update_entry: &update_entry /api/control_panel/dns
            create_entry: *update_entry
        """


class TestConnection(TestCase):
    def test_loading_empty_configuration(self):
        connection = Connection(configuration=None)
        assert_that(connection, all_of(
            has_username(none()),
            has_password(none())
        ))

        assert_that(calling(connection.endpoint_base).with_args(), raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_login).with_args(), raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_establish).with_args(), raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_list_domains).with_args(), raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_domain).with_args("any_domain.local"),
                    raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_update_entry).with_args(), raises(ConnectionConfigurationException))
        assert_that(calling(connection.endpoint_create_entry).with_args(), raises(ConnectionConfigurationException))

    def test_loading_configuration(self):
        connection = Connection(configuration=yaml.safe_load(test_config))

        assert_that(connection, all_of(
            has_username(equal_to("my_username")),
            has_password(equal_to("my_password")),
            has_protocol(equal_to("http")),
            has_base(equal_to("fake_hover.local")),
            has_endpoint("establish", equal_to("/signin")),
            has_endpoint("login", equal_to("/signin/auth.json")),
            has_endpoint("list_domains", equal_to("/api/control_panel/domains")),
            has_endpoint("list_entries", equal_to("/api/control_panel/{domain}/dns")),
            has_endpoint("update_entry", equal_to("/api/control_panel/dns")),
            has_endpoint("create_entry", equal_to("/api/control_panel/dns"))
        ))

    def test_endpoints(self):
        connection = Connection(configuration=yaml.safe_load(test_config))

        assert_that(connection.endpoint_login(), equal_to(f"http://fake_hover.local/signin/auth.json"))
        assert_that(connection.endpoint_establish(), equal_to(f"http://fake_hover.local/signin"))
        assert_that(connection.endpoint_list_domains(), equal_to(f"http://fake_hover.local/api/control_panel/domains"))
        assert_that(connection.endpoint_domain("my_domain.local"),
                    equal_to(f"http://fake_hover.local/api/control_panel/my_domain.local/dns"))
        assert_that(connection.endpoint_update_entry(),
                    equal_to(f"http://fake_hover.local/api/control_panel/dns"))
        assert_that(connection.endpoint_create_entry(),
                    equal_to(f"http://fake_hover.local/api/control_panel/dns"))

    def test_login_with_right_credentials(self):
        connection = Connection(configuration=yaml.safe_load(test_config))

        with HTTMock(http_mock_signin):
            hover_response = connection.log_in()

        assert_that(hover_response.cookies, has_entries(
            dict(hoverauth=anything(), hover_session=anything(), hover_device_id=anything())
        ))

    def test_login_already_logged_in(self):
        connection = Connection(configuration=yaml.safe_load(test_config))

        with HTTMock(http_mock_signin):
            cookies = RequestsCookieJar()
            cookies.update({"hoverauth": "randomauth", "hover_session": "randomsession"})
            hover_response = connection.log_in(cookies=cookies)

        assert_that(hover_response.cookies, has_entries(
            dict(hoverauth=anything(), hover_session=anything())
        ))

    def test_login_with_wrong_credentials(self):
        config = yaml.safe_load(test_config)
        connection = Connection(configuration=config)

        with HTTMock(http_mock_signin):
            assert_that(calling(connection.log_in).with_args(username="username", password="password"),
                        raises(HoverLoginException))

    def test_login_with_missing_credentials(self):
        config = yaml.safe_load(test_config)
        config["credential"]["username"] = None
        config["credential"]["password"] = None
        connection = Connection(configuration=config)

        with HTTMock(http_mock_signin):
            assert_that(calling(connection.log_in).with_args(username="username"),
                        raises(ConnectionConfigurationException, pattern="Missing configuration items: password"))
            assert_that(calling(connection.log_in).with_args(password="password"),
                        raises(ConnectionConfigurationException, pattern="Missing configuration items: username"))
            assert_that(calling(connection.log_in).with_args(),
                        raises(ConnectionConfigurationException, pattern="Missing configuration items: username, "
                                                                         "password"))

    def test_retrieving_domain_list(self):
        connection = Connection(configuration=yaml.safe_load(test_config))
        cookies = RequestsCookieJar()
        cookies.set("hoverauth", "HOVERAUTH")

        with HTTMock(http_mock_domains):
            domain_list_response = connection.list_domains(cookies=cookies)

        assert_that(domain_list_response, all_of(
            has_status_code(200),
        ))

    def test_retrieving_specific_domain_details(self):
        connection = Connection(configuration=yaml.safe_load(test_config))
        cookies = RequestsCookieJar()
        cookies.set("hoverauth", "HOVERAUTH")

        with HTTMock(http_mock_domain):
            domain_list_response = connection.get_domain(domain_name="some_domain1.local", cookies=cookies)

        assert_that(domain_list_response, has_status_code(200))

    def test_update_entry(self):
        connection = Connection(configuration=yaml.safe_load(test_config))
        cookies = RequestsCookieJar()
        cookies.set("hoverauth", "HOVERAUTH")

        with HTTMock(http_mock_entry_update):
            updated_entry = connection.update_entry(
                domain_name="some_domain1.local",
                dns_entry_id="dns1234567",
                content="127.0.0.1",
                ttl=300,
                cookies=cookies,
                record_type=RecordType.A,
                name="hostname"
            )

        assert_that(updated_entry, all_of(
            has_status_code(200),
            has_json_content({
                'succeeded': True,
                'domain': {
                    'id': 'domain-some_domain1.local',
                    'dns_records': [{
                        'id': 'dns1234567',
                        'name': 'hostname',
                        'type': 'A',
                        'content': '127.0.0.1',
                        'ttl': 300,
                        'is_default': False,
                        'can_revert': False
                    }],
                    'name': 'some_domain1.local'
                }
            })
        ))

    def test_create_entry(self):
        connection = Connection(configuration=yaml.safe_load(test_config))
        cookies = RequestsCookieJar()
        cookies.set("hoverauth", "HOVERAUTH")

        with HTTMock(http_mock_entry_create):
            updated_entry = connection.create_entry(
                domain_name="some_domain1.local",
                name="hostname",
                record_type=RecordType.A,
                content="127.0.0.1",
                ttl=300,
                cookies=cookies
            )

        assert_that(updated_entry, all_of(
            has_status_code(200),
            has_json_content({
                "succeeded": True,
                "dns_record": {
                    "id": "dns1234567",
                    "name": "hostname",
                    "type": "A",
                    "content": "127.0.0.1",
                    "ttl": 300,
                    "is_default": False,
                    "can_revert": False}
            })
        ))

    def test_create_mx_record(self):
        connection = Connection(configuration=yaml.safe_load(test_config))
        cookies = RequestsCookieJar()
        cookies.set("hoverauth", "HOVERAUTH")

        with HTTMock(http_mock_entry_create):
            updated_entry = connection.create_mx_entry(
                domain_name="some_domain1.local",
                mail_server="mx.fake_domain.com",
                cookies=cookies,
            )

        assert_that(updated_entry, all_of(
            has_status_code(200),
            has_json_content({
                "succeeded": True,
                "dns_record": {
                    "id": "dns1234567",
                    "name": "@",
                    "type": "MX",
                    "content": "0 mx.fake_domain.com",
                    "ttl": 300,
                    "is_default": False,
                    "can_revert": False}
            })
        ))

    # TODO Add test for cookie expiration
