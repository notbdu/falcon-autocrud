import falcon
import falcon.testing
from .middleware import Middleware
import json
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import Pool
import os
import re
import tempfile
import unittest


Base = declarative_base()

def enable_foreign_keys(dbapi_connection, connection_record):
    # Requires sqlite to be compiled with foreign keys support.  Perhaps we
    # need to start using Postgres for testing?
    enable_fk_sql = """
        PRAGMA foreign_keys = ON;
    """
    result = dbapi_connection.execute(enable_fk_sql)
    result.close()

class BaseTestCase(unittest.TestCase):
    def tearDown(self):
        self.db_session.close()
        self.db_engine.dispose()

        if not self.using_sqlite:
            Session = sessionmaker()
            dsn = re.sub('/autocrudtest$', '', self.dsn)
            tmp_db_engine = create_engine(dsn, isolation_level='AUTOCOMMIT')
            tmp_db_session = Session(bind=tmp_db_engine)
            tmp_db_session.execute('DROP DATABASE autocrudtest')

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.app = falcon.API(
            middleware=[Middleware()],
        )

        Session = sessionmaker()
        if 'AUTOCRUD_DSN' in os.environ and os.environ['AUTOCRUD_DSN'] != '':
            self.dsn = os.environ['AUTOCRUD_DSN']
            self.using_sqlite = True if self.dsn.startswith('sqlite:') else False
        else:
            self.db_file = tempfile.NamedTemporaryFile()
            self.dsn = 'sqlite:///{0}'.format(self.db_file.name)
            self.using_sqlite = True
        if self.dsn.startswith('postgresql+pg8000:'):
            import pg8000

        if not self.using_sqlite:
            tmp_db_engine = create_engine(self.dsn, isolation_level='AUTOCOMMIT')
            tmp_db_session = Session(bind=tmp_db_engine)
            tmp_db_session.execute('CREATE DATABASE autocrudtest')

        if self.dsn.startswith('postgresql+pg8000:'):
            self.dsn += '/autocrudtest'

        self.db_engine  = create_engine(self.dsn, echo=True)
        self.db_session = Session(bind=self.db_engine)

        self.create_test_resources()

        if self.using_sqlite:
            listen(Pool, 'connect', enable_foreign_keys)

        Base.metadata.create_all(self.db_engine)

        self.srmock = falcon.testing.StartResponseMock()

        self.create_common_fixtures()

    def create_test_resources(self):
        pass

    def create_common_fixtures(self):
        pass

    def simulate_request(self, path, *args, **kwargs):
        env = falcon.testing.create_environ(path=path, **kwargs)
        return self.app(env, self.srmock)

    def assertOK(self, response, body=None):
        self.assertEqual(self.srmock.status, '200 OK')
        if body is not None and isinstance(body, dict):
            self.assertEqual(json.loads(response.decode('utf-8')), body)

    def assertCreated(self, response, body=None):
        self.assertEqual(self.srmock.status, '201 Created')
        if body is not None and isinstance(body, dict):
            self.assertEqual(json.loads(response.decode('utf-8')), body)

    def assertBadRequest(self, response, title='Invalid attribute', description='An attribute provided for filtering is invalid'):
        self.assertEqual(self.srmock.status, '400 Bad Request')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        title,
                'description':  description,
            }
        )

    def assertUnauthorized(self, response, description='No credentials supplied'):
        self.assertEqual(self.srmock.status, '401 Unauthorized')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Authentication Required',
                'description':  description,
            }
        )

    def assertForbidden(self, response, description='User does not have access to this resource'):
        self.assertEqual(self.srmock.status, '403 Forbidden')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Permission Denied',
                'description':  description,
            }
        )

    def assertNotFound(self, response):
        self.assertEqual(self.srmock.status, '404 Not Found')
        self.assertEqual(response, [])

    def assertMethodNotAllowed(self, response):
        self.assertEqual(self.srmock.status, '405 Method Not Allowed')
        self.assertEqual(response, [])

    def assertConflict(self, response, description='Unique constraint violated'):
        self.assertEqual(self.srmock.status, '409 Conflict')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Conflict',
                'description':  description,
            }
        )

    def assertInternalServerError(self, response):
        self.assertEqual(self.srmock.status, '500 Internal Server Error')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Internal Server Error',
                'description':  'An internal server error occurred',
            }
        )

