import logging
from urllib.parse import urlsplit

from airbrake import AirbrakeHandler, Airbrake as Client

__version__ = "0.0.1"


from flask.signals import got_request_exception, request_finished
from werkzeug.exceptions import ClientDisconnected


def make_client(client_cls, app, project_id=None, api_key=None,
                environment=None, base_url=None):
    return client_cls(
        project_id, api_key, environment, base_url
    )


EXCLUDE_LOGGER_DEFAULTS = (
    'gunicorn',
)

def get_headers(environ):
    """
    Returns only proper HTTP headers.
    """
    for key, value in environ.items():
        key = str(key)
        if key.startswith('HTTP_') and key not in \
           ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
            yield key[5:].replace('_', '-').title(), value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            yield key.replace('_', '-').title(), value


def get_environ(environ):
    """
    Returns our whitelisted environment variables.
    """
    for key in ('REMOTE_ADDR', 'SERVER_NAME', 'SERVER_PORT'):
        if key in environ:
            yield key, environ[key]

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
    def __init__(self, app=None, logging=False, logging_exclusions=None, level=logging.NOTSET,
                 wrap_wsgi=None, register_signal=True):
        self.logging = logging
        self.logging_exclusions = logging_exclusions
        self.client_cls = Airbrake
        self.level = level
        self.wrap_wsgi = wrap_wsgi
        self.register_signal = register_signal

        if app:
            self.init_app(app)

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return

        self.captureException(exc_info=kwargs.get('exc_info'))

    def get_user_info(self, request):
        """
        Requires implementing decorator
        """
        get_user_implemented = False
        # TODO: Create interface for handling user data
        if not get_user_implemented:
            return

        user_info = {
            'id': None,
        }

        return user_info

    def get_http_info(self, request):
        """
        Determine how to retrieve actual data by using request.mimetype.
        """
        if self.is_json_type(request.mimetype):
            retriever = self.get_json_data
        else:
            retriever = self.get_form_data
        return self.get_http_info_with_retriever(request, retriever)

    def is_json_type(self, content_type):
        return content_type == 'application/json'

    def get_form_data(self, request):
        return request.form

    def get_json_data(self, request):
        return request.data

    def get_http_info_with_retriever(self, request, retriever=None):
        """
        Exact method for getting http_info but with form data work around.
        """
        if retriever is None:
            retriever = self.get_form_data

        urlparts = urlsplit(request.url)

        try:
            data = retriever(request)
        except ClientDisconnected:
            data = {}

        return {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': data,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }

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
            self.client = make_client(self.client_cls, app, self.dsn)

        if self.logging:
            kwargs = {}
            if self.logging_exclusions is not None:
                kwargs['exclude'] = self.logging_exclusions

            setup_logging(AirbrakeHandler(self.client, level=self.level), **kwargs)

        if self.wrap_wsgi:
            app.wsgi_app = None # TODO:

        app.before_request(self.before_request)

        if self.register_signal:
            got_request_exception.connect(self.handle_exception, sender=app)
            request_finished.connect(self.after_request, sender=app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['airbrake'] = self

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        result = self.client.captureException(*args, **kwargs)
        if result:
            self.last_event_id = self.client.get_ident(result)
        else:
            self.last_event_id = None
        return result

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        result = self.client.captureMessage(*args, **kwargs)
        if result:
            self.last_event_id = self.client.get_ident(result)
        else:
            self.last_event_id = None
        return result

    def user_context(self, *args, **kwargs):
        assert self.client, 'user_context called before application configured'
        return self.client.user_context(*args, **kwargs)

    def tags_context(self, *args, **kwargs):
        assert self.client, 'tags_context called before application configured'
        return self.client.tags_context(*args, **kwargs)

    def extra_context(self, *args, **kwargs):
        assert self.client, 'extra_context called before application configured'
        return self.client.extra_context(*args, **kwargs)