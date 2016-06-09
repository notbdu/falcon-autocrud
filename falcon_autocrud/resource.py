from datetime import datetime, time
from decimal import Decimal
import falcon
import falcon.errors
import json
import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.inspection import inspect
import sqlalchemy.sql.sqltypes
import logging
import sys

from .db_session import session_scope

def identify(req, resp, resource, params):
    identifiers = getattr(resource, '__identifiers__', {})
    if req.method in identifiers:
        Identifier = identifiers[req.method]
        Identifier().identify(req, resp, resource, params)

def authorize(req, resp, resource, params):
    authorizers = getattr(resource, '__authorizers__', {})
    if req.method in authorizers:
        Authorizer = authorizers[req.method]
        Authorizer().authorize(req, resp, resource, params)


class UnsupportedGeometryType(Exception):
    pass

try:
    import geoalchemy2.shape
    from geoalchemy2.elements import WKBElement
    from geoalchemy2.types import Geometry
    from shapely.geometry import Point, LineString
    support_geo = True
except ImportError:
    support_geo = False


class BaseResource(object):
    def __init__(self, db_engine, logger=None):
        self.db_engine = db_engine
        if logger is None:
            logger = logging.getLogger('autocrud')
        self.logger = logger

    def filter_by_params(self, resources, params):
        for filter_key, value in params.items():
            filter_parts = filter_key.split('__')
            key = filter_parts[0]
            if len(filter_parts) == 1:
                comparison = '='
            elif len(filter_parts) == 2:
                comparison = filter_parts[1]
            else:
                raise falcon.errors.HTTPBadRequest('Invalid attribute', 'An attribute provided for filtering is invalid')

            attr = getattr(self.model, key, None)
            if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                self.logger.warn('An attribute ({0}) provided for filtering is invalid'.format(key))
                raise falcon.errors.HTTPBadRequest('Invalid attribute', 'An attribute provided for filtering is invalid')
            if comparison == '=':
                resources = resources.filter(attr == value)
            elif comparison == 'null':
                if value != '0':
                    resources = resources.filter(attr.is_(None))
                else:
                    resources = resources.filter(attr.isnot(None))
            elif comparison == 'startswith':
                resources = resources.filter(attr.like('{0}%'.format(value)))
            elif comparison == 'contains':
                resources = resources.filter(attr.like('%{0}%'.format(value)))
            elif comparison == 'lt':
                resources = resources.filter(attr < value)
            elif comparison == 'lte':
                resources = resources.filter(attr <= value)
            elif comparison == 'gt':
                resources = resources.filter(attr > value)
            elif comparison == 'gte':
                resources = resources.filter(attr >= value)
            else:
                raise falcon.errors.HTTPBadRequest('Invalid attribute', 'An attribute provided for filtering is invalid')
        return resources

    def serialize(self, resource):
        def _serialize_value(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            elif isinstance(value, time):
                return value.isoformat()
            elif isinstance(value, Decimal):
                return float(value)
            elif support_geo and isinstance(value, WKBElement):
                value = geoalchemy2.shape.to_shape(value)
                if isinstance(value, Point):
                    return {'x': value.x, 'y': value.y}
                elif isinstance(value, LineString):
                    return [
                        {'x': point[0], 'y': point[1]}
                        for point in list(value.coords)
                    ]
                else:
                    raise UnsupportedGeometryType('Unsupported geometry type {0}'.format(value.geometryType()))
            else:
                return value
        attrs = inspect(self.model).attrs
        return {
            attr: _serialize_value(getattr(resource, attr)) for attr in attrs.keys() if isinstance(attrs[attr], ColumnProperty)
        }

class CollectionResource(BaseResource):
    """
    Provides CRUD facilities for a resource collection.
    """
    def deserialize(self, path_data, body_data):
        mapper      = inspect(self.model)
        attributes  = {}

        for key, value in path_data.items():
            key = getattr(self, 'attr_map', {}).get(key, key)
            if getattr(self.model, key, None) is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
            attributes[key] = value

        for key, value in body_data.items():
            column = mapper.columns[key]
            if isinstance(column.type, sqlalchemy.sql.sqltypes.DateTime):
                attributes[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ') if value is not None else None
            elif isinstance(column.type, sqlalchemy.sql.sqltypes.Time):
                if value is not None:
                    hour, minute, second = value.split(':')
                    attributes[key] = time(int(hour), int(minute), int(second))
                else:
                    attributes[key] = None
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POINT':
                point           = Point(value['x'], value['y'])
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(point.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'LINESTRING':
                line = LineString([point['x'], point['y']] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(line.wkb, srid=4326)
            else:
                attributes[key] = value
        return attributes

    def get_filter(self, req, resp, query, *args, **kwargs):
        return query

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_get(self, req, resp, *args, **kwargs):
        """
        Return a collection of items.
        """
        with session_scope(self.db_engine) as db_session:
            resources = db_session.query(self.model)
            for key, value in kwargs.items():
                key = getattr(self, 'attr_map', {}).get(key, key)
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)

            resources = self.get_filter(
                req, resp,
                self.filter_by_params(resources, req.params),
                *args, **kwargs
            )

            resp.status = falcon.HTTP_OK
            req.context['result'] = {
                'data': [
                    self.serialize(resource) for resource in resources
                ],
            }

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_post(self, req, resp, *args, **kwargs):
        """
        Add an item to the collection.
        """
        attributes = self.deserialize(kwargs, req.context['doc'] if 'doc' in req.context else None)

        defaults = getattr(self, 'post_defaults', {})
        for key, setter in defaults.items():
            if key not in attributes:
                attributes[key] = setter(req, resp, attributes)

        resource = self.model(**attributes)

        with session_scope(self.db_engine) as db_session:
            db_session.add(resource)
            try:
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                # Cases such as unallowed NULL value should have been checked
                # before we got here (e.g. validate against schema
                # using falconjsonio) - therefore assume this is a UNIQUE
                # constraint violation
                db_session.rollback()
                raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
            except sqlalchemy.exc.ProgrammingError as err:
                db_session.rollback()
                if err.orig.args[1] == '23505':
                    raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
                else:
                    raise
            except:
                db_session.rollback()
                raise

            resp.status = falcon.HTTP_CREATED
            req.context['result'] = {
                'data': self.serialize(resource),
            }

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_patch(self, req, resp, *args, **kwargs):
        """
        Update a collection.

        For now, it only supports adding entities to the collection, like this:

        {
            'patches': [
                {'op': 'add', 'path': '/', 'value': {'name': 'Jim', 'age', 25}},
                {'op': 'add', 'path': '/', 'value': {'name': 'Bob', 'age', 28}}
            ]
        }

        """
        mapper  = inspect(self.model)
        patches = req.context['doc']['patches']

        with session_scope(self.db_engine) as db_session:
            for index, patch in enumerate(patches):
                # Only support adding entities in a collection patch, for now
                if 'op' not in patch or patch['op'] not in ['add']:
                    raise falcon.errors.HTTPBadRequest('Invalid patch', 'Patch {0} is not valid'.format(index))
                if patch['op'] == 'add':
                    if 'path' not in patch or patch['path'] != '/':
                        raise falcon.errors.HTTPBadRequest('Invalid patch', 'Patch {0} is not valid for op {1}'.format(index, patch['op']))
                    try:
                        patch_value = patch['value']
                    except KeyError:
                        raise falcon.errors.HTTPBadRequest('Invalid patch', 'Patch {0} is not valid for op {1}'.format(index, patch['op']))
                    args = {}
                    for key, value in kwargs.items():
                        key = getattr(self, 'attr_map', {}).get(key, key)
                        if getattr(self.model, key, None) is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                            self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                            raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                        args[key] = value
                    for key, value in patch_value.items():
                        if isinstance(mapper.columns[key].type, sqlalchemy.sql.sqltypes.DateTime):
                            args[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
                        else:
                            args[key] = value
                    resource = self.model(**args)
                    db_session.add(resource)

            try:
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                # Cases such as unallowed NULL value should have been checked
                # before we got here (e.g. validate against schema
                # using falconjsonio) - therefore assume this is a UNIQUE
                # constraint violation
                db_session.rollback()
                raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
            except sqlalchemy.exc.ProgrammingError as err:
                db_session.rollback()
                if err.orig.args[1] == '23505':
                    raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
                else:
                    raise
            except:
                db_session.rollback()
                raise

        resp.status = falcon.HTTP_OK
        req.context['result'] = {}

class SingleResource(BaseResource):
    """
    Provides CRUD facilities for a single resource.
    """
    def deserialize(self, data):
        mapper      = inspect(self.model)
        attributes  = {}

        for key, value in data.items():
            column = mapper.columns[key]
            if isinstance(column.type, sqlalchemy.sql.sqltypes.DateTime):
                attributes[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ') if value is not None else None
            elif isinstance(column.type, sqlalchemy.sql.sqltypes.Time):
                if value is not None:
                    hour, minute, second = value.split(':')
                    attributes[key] = time(int(hour), int(minute), int(second))
                else:
                    attributes[key] = None
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POINT':
                point           = Point(value['x'], value['y'])
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(point.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'LINESTRING':
                line = LineString([point['x'], point['y']] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(line.wkb, srid=4326)
            else:
                attributes[key] = value

        return attributes

    def get_filter(self, req, resp, query, *args, **kwargs):
        return query

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_get(self, req, resp, *args, **kwargs):
        """
        Return a single item.
        """
        with session_scope(self.db_engine) as db_session:
            resources = db_session.query(self.model)
            for key, value in kwargs.items():
                key = getattr(self, 'attr_map', {}).get(key, key)
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)

            resources = self.get_filter(req, resp, resources, *args, **kwargs)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for get of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            resp.status = falcon.HTTP_OK
            req.context['result'] = {
                'data': self.serialize(resource),
            }

    def delete_precondition(self, req, resp, query, *args, **kwargs):
        return query

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_delete(self, req, resp, *args, **kwargs):
        """
        Delete a single item.
        """
        with session_scope(self.db_engine) as db_session:
            resources = db_session.query(self.model)
            for key, value in kwargs.items():
                key = getattr(self, 'attr_map', {}).get(key, key)
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for patch of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            resources = self.delete_precondition(
                req, resp,
                self.filter_by_params(resources, req.params),
                *args, **kwargs
            )

            try:
                deleted = resources.delete()
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                # As far we I know, this should only be caused by foreign key constraint being violated
                db_session.rollback()
                raise falcon.errors.HTTPConflict('Conflict', 'Other content links to this')
            except sqlalchemy.exc.ProgrammingError as err:
                db_session.rollback()
                if err.orig.args[1] == '23503':
                    raise falcon.errors.HTTPConflict('Conflict', 'Other content links to this')
                else:
                    raise

            if deleted == 0:
                raise falcon.errors.HTTPConflict('Conflict', 'Resource found but conditions violated')
            elif deleted > 1:
                db_session.rollback()
                self.logger.error('Programming error: multiple results found for delete of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

        resp.status = falcon.HTTP_OK
        req.context['result'] = {}

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_put(self, req, resp, *args, **kwargs):
        """
        Update an item in the collection.
        """
        with session_scope(self.db_engine) as db_session:
            resources = db_session.query(self.model)
            for key, value in kwargs.items():
                key = getattr(self, 'attr_map', {}).get(key, key)
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for put of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            attributes = self.deserialize(req.context['doc'])

            defaults = getattr(self, 'put_defaults', {})
            for key, setter in defaults.items():
                if key not in attributes:
                    attributes[key] = setter(req, resp, attributes)

            for key, value in attributes.items():
                setattr(resource, key, value)

            db_session.add(resource)
            try:
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                # Cases such as unallowed NULL value should have been checked
                # before we got here (e.g. validate against schema
                # using falconjsonio) - therefore assume this is a UNIQUE
                # constraint violation
                db_session.rollback()
                raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
            except sqlalchemy.exc.ProgrammingError as err:
                db_session.rollback()
                if err.orig.args[1] == '23505':
                    raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
                else:
                    raise
            except:
                db_session.rollback()
                raise

            resp.status = falcon.HTTP_OK
            req.context['result'] = {
                'data': self.serialize(resource),
            }

    def patch_precondition(self, req, resp, query, *args, **kwargs):
        return query

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_patch(self, req, resp, *args, **kwargs):
        """
        Update part of an item in the collection.
        """
        with session_scope(self.db_engine) as db_session:
            resources = db_session.query(self.model)
            for key, value in kwargs.items():
                key = getattr(self, 'attr_map', {}).get(key, key)
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for patch of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            resources = self.patch_precondition(
                req, resp,
                self.filter_by_params(resources, req.params),
                *args, **kwargs
            )

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPConflict('Conflict', 'Resource found but conditions violated')

            attributes = self.deserialize(req.context['doc'])

            defaults = getattr(self, 'patch_defaults', {})
            for key, setter in defaults.items():
                if key not in attributes:
                    attributes[key] = setter(req, resp, attributes)

            for key, value in attributes.items():
                setattr(resource, key, value)

            db_session.add(resource)
            try:
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                # Cases such as unallowed NULL value should have been checked
                # before we got here (e.g. validate against schema
                # using falconjsonio) - therefore assume this is a UNIQUE
                # constraint violation
                db_session.rollback()
                raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
            except sqlalchemy.exc.ProgrammingError as err:
                db_session.rollback()
                if err.orig.args[1] == '23505':
                    raise falcon.errors.HTTPConflict('Conflict', 'Unique constraint violated')
                else:
                    raise
            except:
                db_session.rollback()
                raise

            resp.status = falcon.HTTP_OK
            req.context['result'] = {
                'data': self.serialize(resource),
            }
