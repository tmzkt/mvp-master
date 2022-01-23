import logging
from django.utils.deprecation import MiddlewareMixin
import urllib
from django.http import HttpResponse

logger = logging.getLogger('django')


class LogRestMiddleware(MiddlewareMixin):
    """Middleware to log every request/response.
    Is not triggered when the request/response is managed using the cache
    """

    def log_request(self, request):
        pass
        """Log the request"""
        user = str(getattr(request, 'user', ''))
        method = str(getattr(request, 'method', '')).upper()
        request_path = str(getattr(request, 'path', ''))
        query_params = str(["%s: %s" % (k, v) for k, v in request.headers.items()])
        body = str(getattr(request, 'body', ''))
        # query_params = query_params if query_params else ''
        #
        logger.info("API Request: (%s) [%s] %s %s %s", user, method, request_path, query_params, body)
        # logger.info('Request Body: {}'.format(type(getattr(request, 'body', ''))))
        # logger.info('Request Body: {}'.format(getattr(request, 'body', '')))
        # logger.info('Request Body: {}'.format(dir(request)))
        # # logger.info('Request Cokkies: {}'.format(getattr(request, 'COOKIES', '')))
        # logger.info('Request Headers: {}'.format(getattr(request, 'headers', '')))

    def log_response(self, request, response):
        pass
        """Log the response using values from the request"""
        user = str(getattr(request, 'user', ''))
        method = str(getattr(request, 'method', '')).upper()
        status_code = str(getattr(response, 'status_code', ''))
        status_text = str(getattr(response, 'status_text', ''))
        request_path = str(getattr(request, 'path', ''))
        size = str(len(response.content))

        logger.info("API Response: (%s) [%s] %s - %s (%s / %s)", user, method, request_path, status_code, status_text,
                    size
                    )
        # logger.info('Content: {}'.format(response.content))

    def process_response(self, request, response):
        """Method call when the middleware is used in the `MIDDLEWARE_CLASSES` option in the settings. Django < 1.10"""
        self.log_request(request)
        self.log_response(request, response)
        return response

    def __call__(self, request):
        """Method call when the middleware is used in the `MIDDLEWARE` option in the settings (Django >= 1.10)"""
        self.log_request(request)
        response = self.get_response(request)
        self.log_response(request, response)
        return response