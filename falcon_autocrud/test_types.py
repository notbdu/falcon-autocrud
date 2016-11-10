import json

from sqlalchemy import Column, Date, DateTime, Integer, String
from .test_base import Base, BaseTestCase

from .resource import CollectionResource, SingleResource

class Foo(Base):
    __tablename__ = 'foos'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    date        = Column(Date)
    datetime    = Column(DateTime)
    localtime   = Column(DateTime)

class FooCollectionResource(CollectionResource):
    model = Foo
    methods = ['POST', 'GET']
    naive_datetimes = ['localtime']

class FooResource(SingleResource):
    model = Foo
    methods = ['PUT', 'PATCH', 'GET']
    naive_datetimes = ['localtime']


class TypeTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/foos', FooCollectionResource(self.db_engine))
        self.app.add_route('/foos/{id}', FooResource(self.db_engine))

    def test_date_and_datetime(self):
        response, = self.simulate_request('/foos', method='POST', body=json.dumps({'name': 'foo', 'date': '2016-10-01', 'datetime': '2016-10-01T13:00:00Z', 'localtime': '2016-12-25T08:00:00'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id': 1,
                'name': 'foo',
                'date': '2016-10-01',
                'datetime': '2016-10-01T13:00:00Z',
                'localtime': '2016-12-25T08:00:00',
            }
        })

        response, = self.simulate_request('/foos', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': [
                {
                    'id': 1,
                    'name': 'foo',
                    'date': '2016-10-01',
                    'datetime': '2016-10-01T13:00:00Z',
                    'localtime': '2016-12-25T08:00:00',
                }
            ],
        })

        response, = self.simulate_request('/foos/1', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id': 1,
                'name': 'foo',
                'date': '2016-10-01',
                'datetime': '2016-10-01T13:00:00Z',
                'localtime': '2016-12-25T08:00:00',
            }
        })

        response, = self.simulate_request('/foos/1', method='PUT', body=json.dumps({'name': 'bar', 'date': '2016-10-02', 'datetime': '2016-10-02T14:00:00Z', 'localtime': '2016-12-25T09:00:00'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id': 1,
                'name': 'bar',
                'date': '2016-10-02',
                'datetime': '2016-10-02T14:00:00Z',
                'localtime': '2016-12-25T09:00:00',
            }
        })

        response, = self.simulate_request('/foos/1', method='PATCH', body=json.dumps({'name': 'baz', 'date': '2016-10-03', 'datetime': '2016-10-03T15:00:00Z', 'localtime': '2016-12-25T10:00:00'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id': 1,
                'name': 'baz',
                'date': '2016-10-03',
                'datetime': '2016-10-03T15:00:00Z',
                'localtime': '2016-12-25T10:00:00',
            }
        })
