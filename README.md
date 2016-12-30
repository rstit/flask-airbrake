Flask-Airbrake
===============================
[![Build Status](https://travis-ci.org/rstit/flask-airbrake.svg?branch=master)](https://travis-ci.org/rstit/flask-airbrake)

version number: 0.0.1

contributor: Piotr Poteralski

Overview
--------

Flask extension for Airbrake

Installation
--------------------

To install use pip:
```bash
$ pip install Flask-Airbrake
```

Or clone the repo:
```bash
$ git clone https://github.com/rstit/flask-airbrake.git
$ python setup.py install
``` 
Usage
-----
The first thing you’ll need to do is setup config:
```python
AIRBRAKE_API_KEY = os_env.get('AIRBRAKE_API_KEY')
AIRBRAKE_PROJECT_ID = os_env.get('AIRBRAKE_PROJECT_ID')
```

Then initialize Airbrake under your application:
```python
from flask_airbrake import Airbrake
airbrake = Airbrake()

def create_app():
    app = Flask(__name__)
    airbrake.init_app(app)
    return app
```
You can implement usergetter for sending custom user info from you auth implementation:
```python
@airbrake.usergetter
def get_user_dict(*args, **kwargs):
    try:
        user = get_current_user()
        return {
            "full_name": user.full_name,
            "id": user.id,
            "email": user.email,
            "token": user.token.access_token
        }
    except Exception:
        return {"error": "Can not get user info"}
```
Contributing
------------

TBD

TODO
------------
* Wrap the WSGI application (Airbrake Middleware).
* Unittests
* Request Parser
* Sphinx Docs
