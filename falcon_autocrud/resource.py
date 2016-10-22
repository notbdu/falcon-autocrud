from datetime import datetime, time
from decimal import Decimal
import falcon
import falcon.errors
import json
import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import make_transient
import sqlalchemy.sql.sqltypes
import uuid
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
    from shapely.geometry import Point, LineString, Polygon
    support_geo = True
except ImportError:
    support_geo = False


class BaseResource(object):
    def __init__(self, db_engine, logger=None, sessionmaker_=sessionmaker, sessionmaker_kwargs={}):
        self.db_engine = db_engine
        self.sessionmaker = sessionmaker_
        self.sessionmaker_kwargs = sessionmaker_kwargs
        if logger is None:
            logger = logging.getLogger('autocrud')
        self.logger = logger

    def filter_by_params(self, resources, params):
        for filter_key, value in params.items():
            if filter_key.startswith('__'):
                # Not a filtering parameter
                continue
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

    def serialize(self, resource, response_fields=None, geometry_axes=None):
        attrs = inspect(resource.__class__).attrs
        def _serialize_value(name, value):
            if isinstance(value, uuid.UUID):
                return value.hex
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            elif isinstance(value, time):
                return value.isoformat()
            elif isinstance(value, Decimal):
                return float(value)
            elif support_geo and isinstance(value, WKBElement):
                value = geoalchemy2.shape.to_shape(value)
                if isinstance(value, Point):
                    axes = (geometry_axes or {}).get(name, ['x', 'y'])
                    return {axes[0]: value.x, axes[1]: value.y}
                elif isinstance(value, LineString):
                    axes = (geometry_axes or {}).get(name, ['x', 'y'])
                    return [
                        {axes[0]: point[0], axes[1]: point[1]}
                        for point in list(value.coords)
                    ]
                elif isinstance(value, Polygon):
                    axes = (geometry_axes or {}).get(name, ['x', 'y'])
                    return [
                        {axes[0]: point[0], axes[1]: point[1]}
                        for point in list(value.boundary.coords)
                    ]
                else:
                    raise UnsupportedGeometryType('Unsupported geometry type {0}'.format(value.geometryType()))
            else:
                return value
        if response_fields is None:
            response_fields = attrs.keys()
        return {
            attr: _serialize_value(attr, getattr(resource, attr)) for attr in response_fields if isinstance(attrs[attr], ColumnProperty)
        }

    def apply_arg_filter(self, req, resp, resources, kwargs):
        for key, value in kwargs.items():
            key = getattr(self, 'attr_map', {}).get(key, key)
            if callable(key):
                resources = key(req, resp, resources, **kwargs)
            else:
                attr = getattr(self.model, key, None)
                if attr is None or not isinstance(inspect(self.model).attrs[key], ColumnProperty):
                    self.logger.error("Programming error: {0}.attr_map['{1}'] does not exist or is not a column".format(self.model, key))
                    raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                resources = resources.filter(attr == value)
        return resources

    def apply_default_attributes(self, defaults_type, req, resp, attributes):
        defaults = getattr(self, defaults_type, {})
        for key, setter in defaults.items():
            if key not in attributes:
                attributes[key] = setter(req, resp, attributes)

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
            if isinstance(getattr(self.model, key, None), property):
                # Value is set using a function, so we cannot tell what type it will be
                attributes[key] = value
                continue
            try:
                column = mapper.columns[key]
            except KeyError:
                # Assume programmer has done their job of filtering out invalid
                # columns, and that they are going to use this field for some
                # custom purpose
                continue
            if isinstance(column.type, sqlalchemy.sql.sqltypes.DateTime):
                attributes[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ') if value is not None else None
            elif isinstance(column.type, sqlalchemy.sql.sqltypes.Time):
                if value is not None:
                    hour, minute, second = value.split(':')
                    attributes[key] = time(int(hour), int(minute), int(second))
                else:
                    attributes[key] = None
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POINT':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                point   = Point(value[axes[0]], value[axes[1]])
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(point.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'LINESTRING':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                line    = LineString([point[axes[0]], point[axes[1]]] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(line.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POLYGON':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                polygon = Polygon([point[axes[0]], point[axes[1]]] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(polygon.wkb, srid=4326)
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
        if 'GET' not in getattr(self, 'methods', ['GET', 'POST', 'PATCH']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'POST', 'PATCH']))

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            resources = self.apply_arg_filter(req, resp, db_session.query(self.model), kwargs)

            resources = self.filter_by_params(
                self.get_filter(
                    req, resp,
                    resources,
                    *args, **kwargs
                ),
                req.params
            )

            sort                = getattr(self, 'default_sort', None)
            using_default_sort  = True
            if '__sort' in req.params:
                using_default_sort = False
                sort = req.get_param_as_list('__sort')
            if sort is not None:
                order_fields = []
                for field_name in sort:
                    reverse = False
                    if field_name[0] == '-':
                        field_name = field_name[1:]
                        reverse = True
                    attr = getattr(self.model, field_name, None)
                    if attr is None or not isinstance(inspect(self.model).attrs[field_name], ColumnProperty):
                        if using_default_sort:
                            self.logger.error("Programming error: Sort field {0}.{1} does not exist or is not a column".format(self.model, field_name))
                            raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')
                        else:
                            raise falcon.errors.HTTPBadRequest('Invalid attribute', 'An attribute provided for sorting is invalid')
                    if reverse:
                        order_fields.append(attr.desc())
                    else:
                        order_fields.append(attr)
                resources = resources.order_by(*order_fields)
            count = None
            if req.get_param_as_int('__offset'):
                count     = resources.count()
                resources = resources.offset(req.get_param_as_int('__offset'))
            if req.get_param_as_int('__limit'):
                if count is None:
                    count     = resources.count()
                resources = resources.limit(req.get_param_as_int('__limit'))

            resp.status = falcon.HTTP_OK
            result = {
                'data': [
                    self.serialize(resource, getattr(self, 'response_fields', None), getattr(self, 'geometry_axes', {})) for resource in resources
                ],
            }
            if '__offset' in req.params or '__limit' in req.params:
                result['meta'] = {'total': count}
                if '__offset' in req.params:
                    result['meta']['offset'] = req.get_param_as_int('__offset')
                if '__limit' in req.params:
                    result['meta']['limit'] = req.get_param_as_int('__limit')
            req.context['result'] = result

            after_get = getattr(self, 'after_get', None)
            if after_get is not None:
                after_get(req, resp, resources, *args, **kwargs)

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_post(self, req, resp, *args, **kwargs):
        """
        Add an item to the collection.
        """
        if 'POST' not in getattr(self, 'methods', ['GET', 'POST', 'PATCH']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'POST', 'PATCH']))

        attributes = self.deserialize(kwargs, req.context['doc'] if 'doc' in req.context else None)

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            self.apply_default_attributes('post_defaults', req, resp, attributes)

            resource = self.model(**attributes)

            before_post = getattr(self, 'before_post', None)
            if before_post is not None:
                self.before_post(req, resp, db_session, resource, *args, **kwargs)

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
                'data': self.serialize(resource, getattr(self, 'response_fields', None), getattr(self, 'geometry_axes', {})),
            }

            after_post = getattr(self, 'after_post', None)
            if after_post is not None:
                after_post(req, resp, resource)

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
        if 'PATCH' not in getattr(self, 'methods', ['GET', 'POST', 'PATCH']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'POST', 'PATCH']))

        mapper  = inspect(self.model)
        patches = req.context['doc']['patches']

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
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

        after_patch = getattr(self, 'after_patch', None)
        if after_patch is not None:
            after_patch(req, resp, *args, **kwargs)

class SingleResource(BaseResource):
    """
    Provides CRUD facilities for a single resource.
    """
    def deserialize(self, data):
        mapper      = inspect(self.model)
        attributes  = {}

        for key, value in data.items():
            if isinstance(getattr(self.model, key, None), property):
                # Value is set using a function, so we cannot tell what type it will be
                attributes[key] = value
                continue
            try:
                column = mapper.columns[key]
            except KeyError:
                # Assume programmer has done their job of filtering out invalid
                # columns, and that they are going to use this field for some
                # custom purpose
                continue
            if isinstance(column.type, sqlalchemy.sql.sqltypes.DateTime):
                attributes[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ') if value is not None else None
            elif isinstance(column.type, sqlalchemy.sql.sqltypes.Time):
                if value is not None:
                    hour, minute, second = value.split(':')
                    attributes[key] = time(int(hour), int(minute), int(second))
                else:
                    attributes[key] = None
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POINT':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                point   = Point(value[axes[0]], value[axes[1]])
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(point.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'LINESTRING':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                line    = LineString([point[axes[0]], point[axes[1]]] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(line.wkb, srid=4326)
            elif support_geo and isinstance(column.type, Geometry) and column.type.geometry_type == 'POLYGON':
                axes    = getattr(self, 'geometry_axes', {}).get(key, ['x', 'y'])
                polygon = Polygon([point[axes[0]], point[axes[1]]] for point in value)
                # geoalchemy2.shape.from_shape uses buffer() which causes INSERT to fail
                attributes[key] = WKBElement(polygon.wkb, srid=4326)
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
        if 'GET' not in getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']))

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            resources = self.apply_arg_filter(req, resp, db_session.query(self.model), kwargs)

            resources = self.get_filter(req, resp, resources, *args, **kwargs)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for get of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            resp.status = falcon.HTTP_OK
            result = {
                'data': self.serialize(resource, getattr(self, 'response_fields', None), getattr(self, 'geometry_axes', {})),
            }
            if '__included' in req.params:
                allowed_included = getattr(self, 'allowed_included', {})
                result['included'] = []
                for included in req.get_param_as_list('__included'):
                    if included not in allowed_included:
                        raise falcon.errors.HTTPBadRequest('Invalid parameter', 'The "__included" parameter includes invalid entities')
                    included_resources  = allowed_included[included]['link'](resource)
                    response_fields     = allowed_included[included].get('response_fields')
                    geometry_axes       = allowed_included[included].get('geometry_axes')

                    for included_resource in included_resources:
                        primary_key, = [
                            attr
                            for attr in inspect(included_resource.__class__).attrs.values()
                            if isinstance(attr, ColumnProperty) and attr.columns[0].primary_key
                        ]
                        result['included'].append({
                            'id':           getattr(resource, primary_key.key),
                            'type':         included,
                            'attributes':   self.serialize(included_resource, response_fields, geometry_axes),
                        })

            req.context['result'] = result

            after_get = getattr(self, 'after_get', None)
            if after_get is not None:
                after_get(req, resp, resource, *args, **kwargs)

    def delete_precondition(self, req, resp, query, *args, **kwargs):
        return query

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_delete(self, req, resp, *args, **kwargs):
        """
        Delete a single item.
        """
        if 'DELETE' not in getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']))

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            resources = self.apply_arg_filter(req, resp, db_session.query(self.model), kwargs)

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
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPConflict('Conflict', 'Resource found but conditions violated')
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for delete of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            try:
                mark_deleted = getattr(self, 'mark_deleted', None)
                if mark_deleted is not None:
                    mark_deleted(req, resp, resource, *args, **kwargs)
                    db_session.add(resource)
                else:
                    make_transient(resource)
                    resources.delete()
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

            resp.status = falcon.HTTP_OK
            req.context['result'] = {}

            after_delete = getattr(self, 'after_delete', None)
            if after_delete is not None:
                after_delete(req, resp, resource, *args, **kwargs)


    @falcon.before(identify)
    @falcon.before(authorize)
    def on_put(self, req, resp, *args, **kwargs):
        """
        Update an item in the collection.
        """
        if 'PUT' not in getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']))

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            resources = self.apply_arg_filter(req, resp, db_session.query(self.model), kwargs)

            try:
                resource = resources.one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise falcon.errors.HTTPNotFound()
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.logger.error('Programming error: multiple results found for put of model {0}'.format(self.model))
                raise falcon.errors.HTTPInternalServerError('Internal Server Error', 'An internal server error occurred')

            attributes = self.deserialize(req.context['doc'])

            self.apply_default_attributes('put_defaults', req, resp, attributes)

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
                'data': self.serialize(resource, getattr(self, 'response_fields', None), getattr(self, 'geometry_axes', {})),
            }

            after_put = getattr(self, 'after_put', None)
            if after_put is not None:
                after_put(req, resp, resource, *args, **kwargs)

    def patch_precondition(self, req, resp, query, *args, **kwargs):
        return query

    def modify_patch(self, req, resp, resource, *args, **kwargs):
        pass

    @falcon.before(identify)
    @falcon.before(authorize)
    def on_patch(self, req, resp, *args, **kwargs):
        """
        Update part of an item in the collection.
        """
        if 'PATCH' not in getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']):
            raise falcon.errors.HTTPMethodNotAllowed(getattr(self, 'methods', ['GET', 'PUT', 'PATCH', 'DELETE']))

        with session_scope(self.db_engine, sessionmaker_=self.sessionmaker, **self.sessionmaker_kwargs) as db_session:
            resources = self.apply_arg_filter(req, resp, db_session.query(self.model), kwargs)

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

            self.apply_default_attributes('patch_defaults', req, resp, attributes)

            for key, value in attributes.items():
                setattr(resource, key, value)

            self.modify_patch(req, resp, resource, *args, **kwargs)

            before_patch = getattr(self, 'before_patch', None)
            if before_patch is not None:
                self.before_patch(req, resp, db_session, resource, *args, **kwargs)

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
                'data': self.serialize(resource, getattr(self, 'response_fields', None), getattr(self, 'geometry_axes', {})),
            }

            after_patch = getattr(self, 'after_patch', None)
            if after_patch is not None:
                after_patch(req, resp, resource, *args, **kwargs)
