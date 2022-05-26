import json
import re
import uuid
from urllib.parse import SplitResult

from httmock import urlmatch, response
from requests import PreparedRequest, Request, Response

HOVER_TEST_DOMAIN = "fake_hover.local"
HOVER_LIST_DOMAINS = {
    "succeeded": True,
    "domains": [
        {
            "id": "domain-some_domain1.local",
            "name": "some_domain1.local",
            "status": "active",
            "expiry_date": "2022-05-19",
            "registration_date": "2021-07-23",
            "whois_privacy": "on",
            "locked": "on",
            "autorenew": "off",
            "renewal_pricing": {},
            "nameservers": [
                "ns1.hover.com",
                "ns2.hover.com"
            ],
            "mailboxes_provisioned": 0,
            "mailboxes_allocated": 0,
            "admin_email": "email@some_domain0.local",
            "connected_to": None,
            "transferring_in": False,
            "can_bulk_update_contacts": True,
            "irtp_designated_agent": True,
            "admin": {},
            "owner": {},
            "billing": {},
            "tech": {},
            "tld_attributes": {},
            "reg_type": "opensrs"
        },
        {
            "id": "domain-some_domain2.local",
            "name": "some_domain2.local",
            "status": "active",
            "expiry_date": "2022-01-19",
            "registration_date": "2021-01-23",
            "whois_privacy": "on",
            "locked": "on",
            "autorenew": "off",
            "renewal_pricing": {},
            "nameservers": [
                "ns1.hover.com",
                "ns2.hover.com"
            ],
            "mailboxes_provisioned": 0,
            "mailboxes_allocated": 0,
            "admin_email": "email@some_domain0.local",
            "connected_to": None,
            "transferring_in": False,
            "can_bulk_update_contacts": True,
            "irtp_designated_agent": True,
            "admin": {},
            "owner": {},
            "billing": {},
            "tech": {},
            "tld_attributes": {},
            "reg_type": "opensrs"
        },
    ],
    "contact": {}
}
HOVER_DOMAIN_DETAILS = {
    "succeeded": True,
    "domain": {
        "id": "domain-some_domain1.local",
        "name": "some_domain1.local",
        "local_nameservers": True,
        "dns": [
            {"id": "dns1234561",
             "name": "@",
             "type": "TXT",
             "content": "MS=ms12345678",
             "ttl": 900,
             "is_default": False,
             "can_revert": False},
            {"id": "dns1234562",
             "name": "@",
             "type": "TXT",
             "content": "v=spf1 include:spf.protection.outlook.com -all",
             "ttl": 900,
             "is_default": False,
             "can_revert": False},
            {"id": "dns1234563",
             "name": "autodiscover",
             "type": "CNAME",
             "content": "autodiscover.outlook.com",
             "ttl": 900,
             "is_default": False,
             "can_revert": False},
            {"id": "dns1234564",
             "name": "@",
             "type": "MX",
             "content": "0 some-domain1.local.mail.protection.outlook.com",
             "ttl": 900,
             "is_default": False,
             "can_revert": True},
            {"id": "dns1234565",
             "name": "home",
             "type": "A",
             "content": "127.0.0.1",
             "ttl": 300,
             "is_default": False,
             "can_revert": False}]},
    "domains": [
        "some_domain1.local",
        "some_domain2.local"
    ]
}

HOVER_ENTRY_DETAILS = {
    "succeeded": True,
    "domain": {
        "id": None,
        "dns_records": [{
            "id": None,
            "name": None,
            "type": None,
            "content": None,
            "ttl": None,
            "is_default": False,
            "can_revert": False
        }],
        "name": None
    }
}
HOVER_ENTRY_NEW = {
    "succeeded": True,
    "dns_record": {
        "id": None,
        "name": None,
        "type": None,
        "content": None,
        "ttl": None,
        "is_default": False,
        "can_revert": False
    }
}

HOVER_BASE_ERROR = {'succeeded': False}


@urlmatch(netloc=HOVER_TEST_DOMAIN, path="/signin")
def http_mock_signin(url: SplitResult, request: PreparedRequest) -> Response:
    original_request: Request = request.original

    if original_request.method == "POST":
        username = original_request.json.get('username', None)
        password = original_request.json.get('password', None)
        if not session_established(request=original_request):
            return error_401_unauthenticated(request)

        if not is_authenticated(original_request) and not validate_credentials(password, username):
            return error_401_wrong_login(request)

        headers = {"content-type": "application/json"}
        content = dict(succeeded=True, status="completed", url="/control_panel", email_verified=True,
                       email="some_email@mailinator.com", username=original_request.json.get('username', None),
                       email_notifications=dict(renew60before=False, renew30before=True, renew15before=False,
                                                renew7before=True, renew3before=True, renew1before=True,
                                                renew1after=True, renew7after=True, renew10after=False,
                                                newsletters=False, surveys=False)
                       )

        resp = response(status_code=200, content=content, headers=headers, reason=None, elapsed=5, request=request)
        resp.cookies.set("hover_device_id", original_request.cookies.get("hover_device_id", uuid.uuid4().hex))
        resp.cookies.set("hoverauth", original_request.cookies.get("hoverauth", uuid.uuid4().hex))
    elif original_request.method == "GET":
        if is_authenticated(original_request):
            resp = response(status_code=302, request=request)
        else:
            resp = response(status_code=200, request=request)
            resp.cookies.set("hover_session", "SESSION_ID")
    else:
        raise NotImplementedError(original_request.method)

    return resp


@urlmatch(netloc=HOVER_TEST_DOMAIN, path="/api/control_panel/domains")
def http_mock_domains(url: SplitResult, request: PreparedRequest):
    original_request = request.original
    not_authenticated = not is_authenticated(request=original_request)

    if not_authenticated:
        return error_401_unauthenticated(request)

    return response(status_code=200, content=json.dumps(HOVER_LIST_DOMAINS))


@urlmatch(netloc=HOVER_TEST_DOMAIN, path=r'/api/control_panel/.*/dns', method="get")
def http_mock_domain(url: SplitResult, request: PreparedRequest):
    original_request = request.original
    not_authenticated = not is_authenticated(request=original_request)

    if not_authenticated:
        return error_401_unauthenticated(request)

    return response(status_code=200, content=json.dumps(HOVER_DOMAIN_DETAILS))


@urlmatch(netloc=HOVER_TEST_DOMAIN, path="/api/control_panel/dns",
          method="put")
def http_mock_entry_update(url: SplitResult, request: PreparedRequest):
    original_request = request.original
    not_authenticated = not is_authenticated(request=original_request)

    if not_authenticated:
        return error_401_unauthenticated(request)

    dns_records = original_request.json['domain']['dns_records'][0]
    fields = original_request.json['fields']

    HOVER_ENTRY_DETAILS["domain"]["id"] = original_request.json['domain']['id']
    HOVER_ENTRY_DETAILS["domain"]["name"] = re.match(r"domain-(.*)", original_request.json['domain']['id']).group(1)
    HOVER_ENTRY_DETAILS["domain"]["dns_records"][0].update(dict(
        id=dns_records['id'],
        name=dns_records['name'],
        type=dns_records['type'],
        content=fields['content'],
        ttl=fields['ttl']
    ))
    return response(status_code=200, content=(json.dumps(HOVER_ENTRY_DETAILS)))


@urlmatch(netloc=HOVER_TEST_DOMAIN, path="/api/control_panel/dns",
          method="post")
def http_mock_entry_create(url: SplitResult, request: PreparedRequest):
    original_request = request.original
    not_authenticated = not is_authenticated(request=original_request)

    if not_authenticated:
        return error_401_unauthenticated(request)

    HOVER_ENTRY_NEW["dns_record"].update(dict(
        id="dns1234567",
        name=original_request.json['dns_record']['name'],
        content=original_request.json['dns_record']['content'],
        type=original_request.json['dns_record']['type'],
        ttl=original_request.json['dns_record']['ttl']

    ))

    return response(status_code=200, content=json.dumps(HOVER_ENTRY_NEW))


def is_authenticated(request: Request):
    return "hoverauth" in (request.cookies or [])


def session_established(request: Request):
    return "hover_session" in (request.cookies or [])


def device_identified(request: Request):
    return "hover_device_id" in (request.cookies or [])


def error_401_wrong_login(request: PreparedRequest):
    headers = {'content-type': 'application/json'}
    content = {"error": "Invalid username or password."}
    content.update(**HOVER_BASE_ERROR)
    return response(status_code=401, headers=headers, content=content, request=request)


def error_401_unauthenticated(request: PreparedRequest):
    headers = {'content-type': 'application/json'}
    content = {"error_code": "login", "error": "You must login first"}
    content.update(**HOVER_BASE_ERROR)
    return response(status_code=401, headers=headers, content=content, request=request)


def validate_credentials(password, username):
    return username == "my_username" and password == "my_password"
