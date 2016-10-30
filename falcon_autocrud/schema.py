import inspect

class SchemaDecoratorError(Exception): pass

class request_schema(object):
    """
    Decorator to specify the JSON schema required for a request.
    """
    def __init__(self, schema, method_name=None):
        self.schema         = schema
        self.method_name    = method_name

    def __call__(self, klass_or_func):
        if inspect.isclass(klass_or_func):
            if not hasattr(klass_or_func, '__request_schemas__'):
                klass_or_func.__request_schemas__ = {}
            if self.method_name is None:
                raise SchemaDecoratorError("Parameter 'method_name' must be supplied when applying request_schema decorator to a class")
            klass_or_func.__request_schemas__[self.method_name] = self.schema
        else:
            klass_or_func.__request_schema__ = self.schema
        return klass_or_func

class response_schema(object):
    """
    Decorator to specify the JSON schema a response should conform to.
    """
    def __init__(self, schema, method_name = None):
        self.schema         = schema
        self.method_name    = method_name

    def __call__(self, klass_or_func):
        if inspect.isclass(klass_or_func):
            if not hasattr(klass_or_func, '__response_schemas__'):
                klass_or_func.__response_schemas__ = {}
            if self.method_name is None:
                raise SchemaDecoratorError("Parameter 'method_name' must be supplied when applying response_schema decorator to a class")
            klass_or_func.__response_schemas__[self.method_name] = self.schema
        else:
            klass_or_func.__response_schema__ = self.schema
        return klass_or_func
