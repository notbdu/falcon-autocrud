from datetime import datetime, timedelta
import falconjsonio.middleware, falconjsonio.schema
import falcon, falcon.testing
import json
import tempfile
import unittest
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .resource import CollectionResource, SingleResource


Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    employees   = relationship('Employee')

class Employee(Base):
    __tablename__ = 'employees'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    joined      = Column(DateTime())
    company_id  = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company     = relationship('Company', back_populates='employees')

class CompanyCollectionResource(CollectionResource):
    model = Company

class CompanyResource(SingleResource):
    model = Company

class EmployeeCollectionResource(CollectionResource):
    model = Employee

class EmployeeResource(SingleResource):
    model = Employee


class AutoCRUDTest(unittest.TestCase):
    def setUp(self):
        super(AutoCRUDTest, self).setUp()

        self.app = falcon.API(
            middleware=[
                falconjsonio.middleware.RequireJSON(),
                falconjsonio.middleware.JSONTranslator(),
            ],
        )

        self.db_file    = tempfile.NamedTemporaryFile()
        Session         = sessionmaker()
        db_engine       = create_engine('sqlite:///{0}'.format(self.db_file.name))
        self.db_session = Session(bind=db_engine)

        self.app.add_route('/companies', CompanyCollectionResource(self.db_session))
        self.app.add_route('/companies/{id}', CompanyResource(self.db_session))
        self.app.add_route('/employees', EmployeeCollectionResource(self.db_session))
        self.app.add_route('/employees/{id}', EmployeeResource(self.db_session))

        create_sql = """
            CREATE TABLE companies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT UNIQUE NOT NULL
            );
        """
        result = self.db_session.execute(create_sql)
        result.close()

        create_sql = """
            CREATE TABLE employees (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT UNIQUE NOT NULL,
                joined      DATETIME NOT NULL,
                company_id  INTEGER
            );
        """
        result = self.db_session.execute(create_sql)
        result.close()

        self.srmock = falcon.testing.StartResponseMock()

    def simulate_request(self, path, *args, **kwargs):
        env = falcon.testing.create_environ(path=path, **kwargs)
        return self.app(env, self.srmock)

    def assertNotFound(self, response):
        self.assertEqual(self.srmock.status, '404 Not Found')
        self.assertEqual(response, [])

    def assertConflict(self, response):
        self.assertEqual(self.srmock.status, '409 Conflict')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Conflict',
                'description':  'Unique constraint violated',
            }
        )

    def test_empty_collection(self):
        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {'data': []}
        )

    def test_entire_collection(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    }
                ]
            }
        )

    def test_add_resource(self):
        now = datetime.utcnow()
        body = json.dumps({
            'name': 'Alfred',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response, = self.simulate_request('/employees', method='POST', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'company_id': None,
                },
            }
        )

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Alfred',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_add_resource_conflict(self):
        now     = datetime.utcnow()
        then    = now - timedelta(minutes=5)
        self.db_session.add(Employee(name="Alfred", joined=then))
        self.db_session.commit()
        body = json.dumps({
            'name': 'Alfred',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response, = self.simulate_request('/employees', method='POST', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertConflict(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Alfred',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_put_resource(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        body = json.dumps({
            'name':     'Alfred',
            'joined':   '2015-11-01T09:30:12Z',
        })
        response, = self.simulate_request('/employees/1', method='PUT', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': '2015-11-01T09:30:12Z',
                    'company_id': None,
                },
            }
        )

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Alfred',
                        'joined': '2015-11-01T09:30:12Z',
                        'company_id': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_put_resource_conflict(self):
        now     = datetime.utcnow()
        then    = now - timedelta(minutes=5)
        self.db_session.add(Employee(name="Jim", joined=then))
        self.db_session.add(Employee(name="Bob", joined=then))
        self.db_session.commit()

        body = json.dumps({
            'name':   'Bob',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response, = self.simulate_request('/employees/1', method='PUT', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertConflict(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_put_resource_not_found(self):
        now     = datetime.utcnow()
        then    = now - timedelta(minutes=5)
        self.db_session.add(Employee(name="Jim", joined=then))
        self.db_session.commit()

        body = json.dumps({
            'name':   'Bob',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response = self.simulate_request('/employees/2', method='PUT', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertNotFound(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_patch_resource(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        body = json.dumps({
            'name': 'Alfred',
            'joined': '2015-11-01T09:30:12Z',
        })
        response, = self.simulate_request('/employees/1', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': '2015-11-01T09:30:12Z',
                    'company_id': None,
                },
            }
        )

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Alfred',
                        'joined': '2015-11-01T09:30:12Z',
                        'company_id': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_patch_resource_conflict(self):
        now     = datetime.utcnow()
        then    = now - timedelta(minutes=5)
        self.db_session.add(Employee(name="Jim", joined=then))
        self.db_session.add(Employee(name="Bob", joined=then))
        self.db_session.commit()

        body = json.dumps({
            'name': 'Bob',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response, = self.simulate_request('/employees/1', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertConflict(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_patch_resource_not_found(self):
        now     = datetime.utcnow()
        then    = now - timedelta(minutes=5)
        self.db_session.add(Employee(name="Jim", joined=then))
        self.db_session.commit()

        body = json.dumps({
            'name':   'Bob',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        response = self.simulate_request('/employees/2', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertNotFound(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

    def test_single_delete(self):
        now = datetime.now()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {}
        )

        response = self.simulate_request('/employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )


    def test_single_delete_not_found(self):
        now = datetime.now()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response = self.simulate_request('/employees/3', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)

    def test_single_get(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Jim',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'company_id': None,
                },
            }
        )

        response, = self.simulate_request('/employees/2', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   2,
                    'name': 'Bob',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'company_id': None,
                },
            }
        )

    def test_single_get_not_found(self):
        response = self.simulate_request('/employees/3', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)

    def test_subcollection(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees', query_string='name=Jim', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='name=Bob', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id=1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    },
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id=2', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'company_id': None,
                    }
                ]
            }
        )
