
class identify(object):
    """
    Decorator to specify the identifier function/class for a request.
    """
    def __init__(self, identifier, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE']):
        self.identifier = identifier
        self.methods    = methods

    def __call__(self, klass):
        if not hasattr(klass, '__identifiers__'):
            klass.__identifiers__ = {}
        for method in self.methods:
            klass.__identifiers__[method] = self.identifier

        return klass

class authorize(object):
    """
    Decorator to specify the authorizer function/class for a request.
    """
    def __init__(self, authorizer, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE']):
        self.authorizer = authorizer
        self.methods    = methods

    def __call__(self, klass):
        if not hasattr(klass, '__authorizers__'):
            klass.__authorizers__ = {}
        for method in self.methods:
            klass.__authorizers__[method] = self.authorizer

        return klass
