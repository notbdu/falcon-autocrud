from datetime import datetime
import falcon
import falcon.errors
import json
import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy.orm.properties import ColumnProperty
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
        attrs = inspect(self.model).attrs
        return {
            attr: _serialize_value(getattr(resource, attr)) for attr in attrs.keys() if isinstance(attrs[attr], ColumnProperty)
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
        except sqlalchemy.exc.IntegrityError as err:
            # Cases such as unallowed NULL value should have been checked
            # before we got here (e.g. validate against schema
            # using falconjsonio) - therefore assume this is a UNIQUE
            # constraint violation
            self.db_session.rollback()
            raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
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
        attrs = inspect(self.model).attrs
        return {
            attr: _serialize_value(getattr(resource, attr)) for attr in attrs.keys() if isinstance(attrs[attr], ColumnProperty)
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

        try:
            resource = resources.one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise falcon.errors.HTTPNotFound()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise falcon.errors.HTTPInternalServerError()

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

        deleted = resources.delete()

        if deleted == 0:
            raise falcon.errors.HTTPNotFound()
        elif deleted > 1:
            self.db_session.rollback()
            raise falcon.errors.HTTPInternalServerError()

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

        try:
            resource = resources.one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise falcon.errors.HTTPNotFound()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise falcon.errors.HTTPInternalServerError()

        mapper = inspect(self.model)
        for key, value in req.context['doc'].items():
            if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                setattr(resource, key, datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
            else:
                setattr(resource, key, value)

        self.db_session.add(resource)
        try:
            self.db_session.commit()
        except sqlalchemy.exc.IntegrityError as err:
            # Cases such as unallowed NULL value should have been checked
            # before we got here (e.g. validate against schema
            # using falconjsonio) - therefore assume this is a UNIQUE
            # constraint violation
            self.db_session.rollback()
            raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
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

        try:
            resource = resources.one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise falcon.errors.HTTPNotFound()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise falcon.errors.HTTPInternalServerError()

        mapper = inspect(self.model)
        for key, value in req.context['doc'].items():
            if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                setattr(resource, key, datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
            else:
                setattr(resource, key, value)

        self.db_session.add(resource)
        try:
            self.db_session.commit()
        except sqlalchemy.exc.IntegrityError as err:
            # Cases such as unallowed NULL value should have been checked
            # before we got here (e.g. validate against schema
            # using falconjsonio) - therefore assume this is a UNIQUE
            # constraint violation
            self.db_session.rollback()
            raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
        except:
            self.db_session.rollback()
            raise

        resp.status = falcon.HTTP_OK
        req.context['result'] = {
            'data': self.serialize(resource),
        }
