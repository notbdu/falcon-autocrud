import falconjsonio.middleware, falconjsonio.schema
import falcon, falcon.testing
import json
import tempfile
import unittest
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from .resource import CollectionResource, SingleResource


Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id      = Column(Integer, primary_key=True)
    name    = Column(String(50))

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

        self.app.add_route('/employees', EmployeeCollectionResource(self.db_session))
        self.app.add_route('/employees/{employee_id}', EmployeeResource(self.db_session))

        create_sql = """
            CREATE TABLE employees (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL
            );
        """
        result = self.db_session.execute(create_sql)
        result.close()

        self.srmock = falcon.testing.StartResponseMock()

    def simulate_request(self, path, *args, **kwargs):
        env = falcon.testing.create_environ(path=path, **kwargs)
        return self.app(env, self.srmock)

    def test_empty_collection(self):
        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {'data': []}
        )

    def test_entire_collection(self):
        self.db_session.add(Employee(name="Jim"))
        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                    },
                ]
            }
        )

        self.db_session.add(Employee(name="Bob"))
        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                    }
                ]
            }
        )
