from datetime import datetime
import falcon
import json
from sqlalchemy.inspection import inspect
import sqlalchemy.sql.sqltypes


class CollectionResource(object):
    """
    Provides CRUD facilities for a resource collection.
    """
    def __init__(self, db_session):
        self.db_session = db_session

    def serialize(self, resource):
        def _serialize_value(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                return value
        return {
            attr: _serialize_value(getattr(resource, attr)) for attr in inspect(self.model).attrs.keys()
        }

    def on_get(self, req, resp, *args, **kwargs):
        """
        Return a collection of items.
        """
        resources = self.db_session.query(self.model)
        for key, value in kwargs.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )
        for key, value in req.params.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )

        resp.status = falcon.HTTP_OK
        req.context['result'] = {
            'data': [
                self.serialize(resource) for resource in resources
            ],
        }

    def on_post(self, req, resp, *args, **kwargs):
        """
        Add an item to the collection.
        """
        args = {}
        mapper = inspect(self.model)
        for key, value in kwargs.items():
            args[key] = value
        for key, value in req.context['doc'].items():
            if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                args[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            else:
                args[key] = value
        resource = self.model(**args)

        self.db_session.add(resource)
        try:
            self.db_session.commit()
        except:
            self.db_session.rollback()
            raise

        resp.status = falcon.HTTP_CREATED
        req.context['result'] = {
            'data': self.serialize(resource),
        }

class SingleResource(object):
    """
    Provides CRUD facilities for a single resource.
    """
    def __init__(self, db_session):
        self.db_session = db_session

    def serialize(self, resource):
        def _serialize_value(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                return value
        return {
            attr: _serialize_value(getattr(resource, attr)) for attr in inspect(self.model).attrs.keys()
        }

    def on_get(self, req, resp, *args, **kwargs):
        """
        Return a single item.
        """
        resources = self.db_session.query(self.model)
        for key, value in kwargs.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )
        if resources.count() == 0:
            resp.status = falcon.HTTP_NOT_FOUND
            req.context['result'] = {
                'data': None,
            }
            return
        elif resources.count() > 1:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            req.context['result'] = None
            return

        resource = resources[0]
        resp.status = falcon.HTTP_OK
        req.context['result'] = {
            'data': self.serialize(resource),
        }

    def on_delete(self, req, resp, *args, **kwargs):
        """
        Delete a single item.
        """
        resources = self.db_session.query(self.model)
        for key, value in kwargs.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )
        if resources.count() == 0:
            resp.status = falcon.HTTP_NOT_FOUND
            req.context['result'] = {
                'data': None,
            }
            return
        elif resources.count() > 1:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            req.context['result'] = None
            return

        resources.delete()

        resp.status = falcon.HTTP_OK
        req.context['result'] = {}

    def on_put(self, req, resp, *args, **kwargs):
        """
        Update an item in the collection.
        """
        resources = self.db_session.query(self.model)
        for key, value in kwargs.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )
        if resources.count() == 0:
            resp.status = falcon.HTTP_NOT_FOUND
            req.context['result'] = {
                'data': None,
            }
            return
        elif resources.count() > 1:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            req.context['result'] = None
            return

        resource = resources[0]

        mapper = inspect(self.model)
        for key, value in req.context['doc'].items():
            if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                setattr(resource, key, datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
            else:
                setattr(resource, key, value)

        self.db_session.add(resource)
        try:
            self.db_session.commit()
        except:
            self.db_session.rollback()
            raise

        resp.status = falcon.HTTP_OK
        req.context['result'] = {
            'data': self.serialize(resource),
        }

    def on_patch(self, req, resp, *args, **kwargs):
        """
        Update part of an item in the collection.
        """
        resources = self.db_session.query(self.model)
        for key, value in kwargs.items():
            resources = resources.filter(
                getattr(self.model, key) == value
            )
        if resources.count() == 0:
            resp.status = falcon.HTTP_NOT_FOUND
            req.context['result'] = {
                'data': None,
            }
            return
        elif resources.count() > 1:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            req.context['result'] = None
            return

        resource = resources[0]

        mapper = inspect(self.model)
        for key, value in req.context['doc'].items():
            if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                setattr(resource, key, datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
            else:
                setattr(resource, key, value)

        self.db_session.add(resource)
        try:
            self.db_session.commit()
        except:
            self.db_session.rollback()
            raise

        resp.status = falcon.HTTP_OK
        req.context['result'] = {
            'data': self.serialize(resource),
        }
