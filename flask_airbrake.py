# -*- coding: utf-8 -*-
import logging

from airbrake import AirbrakeHandler, Airbrake as Client

__version__ = "0.0.1"

from flask.signals import got_request_exception


def make_client(client_cls, app, environment=None, base_url=None):
    api_key = app.config.get('AIRBRAKE_API_KEY')
    project_id = app.config.get('AIRBRAKE_PROJECT_ID')
    return client_cls(
        project_id, api_key, environment, base_url
    )


EXCLUDE_LOGGER_DEFAULTS = (
    'gunicorn',
)


def setup_logging(handler, exclude=EXCLUDE_LOGGER_DEFAULTS):
    logger = logging.getLogger()
    if handler.__class__ in map(type, logger.handlers):
        return False

    logger.addHandler(handler)

    # Add StreamHandler to airbrake's default so you can catch missed exceptions
    for logger_name in exclude:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

    return True


class Airbrake(object):
    def __init__(self, app=None, logging=False, logging_exclusions=None,
                 level=logging.NOTSET, wrap_wsgi=None, register_signal=True):
        self.logging = logging
        self.logging_exclusions = logging_exclusions
        self.client_cls = Client
        self.client = None
        self.level = level
        self.wrap_wsgi = wrap_wsgi
        self.register_signal = register_signal
        self._usergetter = None

        if app:
            self.init_app(app)

    def init_app(self, app, logging=None, level=None,
                 logging_exclusions=None, wrap_wsgi=None,
                 register_signal=None):
        if level is not None:
            self.level = level

        if wrap_wsgi is not None:
            self.wrap_wsgi = wrap_wsgi
        elif self.wrap_wsgi is None:
            if app and app.debug:
                self.wrap_wsgi = False
            else:
                self.wrap_wsgi = True

        if register_signal is not None:
            self.register_signal = register_signal

        if logging is not None:
            self.logging = logging

        if logging_exclusions is not None:
            self.logging_exclusions = logging_exclusions

        if not self.client:
            self.client = make_client(self.client_cls, app)

        if self.logging:
            kwargs = {}
            if self.logging_exclusions is not None:
                kwargs['exclude'] = self.logging_exclusions
            setup_logging(AirbrakeHandler(self.client, level=self.level),
                          **kwargs)

        if self.wrap_wsgi:
            app.wsgi_app = None  # TODO:

        if self.register_signal:
            got_request_exception.connect(self.handle_exception, sender=app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['airbrake'] = self

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return
        extra = {}
        if self._usergetter:
            extra['user'] = self._usergetter()
        self.capture_exception(exc_info=kwargs.get('exc_info'), extra=extra)

    def capture_exception(self, *args, **kwargs):
        result = self.client.log(*args, **kwargs)
        return result

    def usergetter(self, f):
        """Register a function as the user info getter.

        This decorator is only required for user info in extra::

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
        """
        self._usergetter = f
        return f
