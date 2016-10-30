import falcon
import json
import jsonschema
import logging


def _get_request_schema(req, resource):
    if resource is None or req.method not in ['POST', 'PUT', 'PATCH']:
        return None

    # First try to get schema from method itself
    schema = getattr(
        getattr(resource, {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch'}[req.method], None),
        '__request_schema__',
        None
    # Otherwise, fall back to schema defined directly in class
    ) or getattr(resource, '__request_schemas__', {}).get(
        {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch'}[req.method]
    )
    return schema

def _get_response_schema(resource, req):
    try:
        method_name = {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch', 'GET': 'on_get', 'DELETE': 'on_delete'}[req.method]
    except KeyError:
        return

    # First try to get schema from method itself
    return getattr(
        getattr(resource, method_name, None),
        '__response_schema__',
        None
    # Otherwise, fall back to schema defined directly in class
    ) or getattr(resource, '__response_schemas__', {}).get(method_name)


class _null_handler(logging.Handler):
    def emit(self, record):
        pass

class RequireJSON(object):
    def process_resource(self, req, resp, resource, params):
        if _get_response_schema(resource, req) and not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable('This API supports only JSON-encoded responses')
        if req.method in ('POST', 'PUT', 'PATCH'):
            if _get_request_schema(req, resource) is not None:
                if req.content_type is None or 'application/json' not in req.content_type:
                    raise falcon.HTTPUnsupportedMediaType('This API supports only JSON-encoded requests')

class JSONTranslator(object):
    def __init__(self, logger=None):
        if logger is None:
            # Default to no logging if no logger provided
            logger = logging.getLogger(__name__)
            logger.addHandler(_null_handler())
        self.logger = logger

    def process_resource(self, req, resp, resource, params):
        if resource is None or req.method not in ['POST', 'PUT', 'PATCH']:
            return

        if 'application/json' in req.content_type:
            body = req.stream.read()
            if not body:
                raise falcon.HTTPBadRequest(
                    'Empty request body',
                    'A valid JSON document is required'
                )

            schema = _get_request_schema(req, resource)
            try:
                req.context['doc'] = json.loads(body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError) as error:
                if schema is not None:
                    raise falcon.HTTPBadRequest(
                        'Malformed JSON',
                        'Could not decode the request body.  The JSON was incorrect or not encoded as UTF-8'
                    )
                req.context['doc'] = body

            if schema is not None:
                try:
                    jsonschema.validate(req.context['doc'], schema)
                except jsonschema.exceptions.ValidationError as error:
                    raise falcon.HTTPBadRequest(
                        'Invalid request body',
                        json.dumps({'error': str(error)})
                    )

    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'])

        schema = _get_response_schema(resource, req)
        if schema is None:
            return

        try:
            jsonschema.validate(req.context['result'], schema)
        except jsonschema.exceptions.ValidationError as error:
            method_name = {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch', 'GET': 'on_get', 'DELETE': 'on_delete'}[req.method]
            self.logger.error('Blocking proposed response from being sent from {0}.{1}.{2} to client as it does not match the defined schema: {3}'.format(resource.__module__, resource.__class__.__name__, method_name, str(error)))
            raise falcon.HTTPInternalServerError('Internal Server Error', 'Undisclosed')
