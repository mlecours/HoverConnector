# HoverConnector
HoverConnector is a Python library for dealing with Hover (hover.com) __private API__ to update DNS records.

This "HoverConnector" project allows managing DNS records for domains hosted at Hover. 
It is based on their private API and cannot (obviously) offer any guarantee.

## Notes
### 1. Passthrough 
It is a simple "proxy/passthrough" to the private API.

e.g.: It does not verify for the existence of previous entries when creating a new record. Hover allows some duplicate
entries. Therefore, it is recommended to "list" records before creating one. 

### 2. Returned values
Except for the call to `log_in`, the other calls return the actual `requests.Response`.

i.e.:
- `list_domains`
- `get_domain`
- `update_entry`
- `create_entry`
- `create_mx_entry`

### 3. Configuration file
The provided `config.example.yml` file contains the right information (endpoints and structure) to start making queries. All you need is to set the right username and password in the configuration file and load it as in [Example 2](#example-2).  

## Configuration
It is recommended to use a configuration file and pass the loaded configuration to the Connection constructor. 
(see [Example 2](#example-2))

## Recommandations
It is recommended to save cookies to a local file and to reuse said cookies to avoid receiving a 
"new device connected" for every instantiation of a Connection. 
(see [Example 2](#example-2))

## Limitations
It was built for my current needs and does not support MFA (yet?).

## Installation
For now, the installation process is not straightforward, but here are the two steps:

### 1. Building the wheel
From the project's root folder:
```bash
python setup.py bdist_wheel -b build/bdist -d build/wheel
```

### 2. Installing in a project
With your environment activated:
```bash
pip install /path/to/wheel/hoverconnector-VERSION-py3-none-any.whl
```

## Usage
### Example 1
Basic setup

```python
from hoverconnector.connection import Connection
from hoverconnector import RecordType

connection = Connection(configuration={
    'endpoints': {
        'protocol': 'https',
        'base': 'www.hover.com',
        'establish': '/signin',
        'login': '/signin/auth.json',
        'list_domains': '/api/control_panel/domains',
        'list_entries': '/api/control_panel/{domain}/dns',
        'update_entry': '/api/control_panel/dns',
        'create_entry': '/api/control_panel/dns'
    }
})
connection.log_in(username="USERNAME", password="PASSWORD")
connection.create_entry(domain_name="my-domain-name.local", name="home", record_type=RecordType.A,
                        content="127.0.0.1", ttl=600)

```

### Example 2
Using saved configuration and saved cookies (recommended)

```python
import os
from typing import Union

import requests
import yaml
from requests.cookies import RequestsCookieJar

from hoverconnector.connection import Connection
from hoverconnector import RecordType

config_file = os.path.join(os.path.dirname(__file__), 'config.yml')
with open(config_file, 'r') as f:
    config = yaml.load(f, yaml.SafeLoader)

cookies: Union[RequestsCookieJar, None] = None
cookie_file = os.path.join(os.path.dirname(__file__), 'cookies.yml')
try:
    with open(cookie_file, 'r') as f:
        cookies = yaml.load(f, yaml.CLoader)
except FileNotFoundError as e:
    cookies = RequestsCookieJar()

connection = Connection(config, cookies=cookies)
new_ip = requests.get("https://api.ipify.org?format=json").json()

with open(cookie_file, 'w') as f:
    yaml.dump(connection.log_in().cookies, f, yaml.CDumper)

connection.create_entry(domain_name="my-domain-name.local", name="a_record", record_type=RecordType.A,
                        content=new_ip["ip"], ttl=600)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
