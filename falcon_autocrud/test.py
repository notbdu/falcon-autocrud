from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, Numeric, String, Time

from .resource import CollectionResource, SingleResource

from .test_base import Base, BaseTestCase

from .test_fixtures import Company, Employee


class CompanyCollectionResource(CollectionResource):
    model = Company

class CompanyResource(SingleResource):
    model = Company

class EmployeeCollectionResource(CollectionResource):
    model = Employee

    post_defaults = {
        'caps_name': (lambda req, res, attributes: attributes['name'].upper()),
    }

class EmployeeResource(SingleResource):
    model = Employee

    put_defaults = {
        'caps_name': (lambda req, res, attributes: 'PUT ' + attributes['name'].upper()),
    }
    patch_defaults = {
        'caps_name': (lambda req, res, attributes: 'PATCH ' + attributes['name'].upper()),
    }

class OtherEmployeeResource(SingleResource):
    model = Employee
    attr_map = {
        'employee_id': 'id'
    }

class AutoCRUDTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/companies', CompanyCollectionResource(self.db_engine))
        self.app.add_route('/companies/{id}', CompanyResource(self.db_engine))
        self.app.add_route('/employees', EmployeeCollectionResource(self.db_engine))
        self.app.add_route('/employees/{id}', EmployeeResource(self.db_engine))

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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

    def test_add_resource(self):
        now = datetime.utcnow()
        body = json.dumps({
            'name': 'Alfred',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'left': None,
            'pay_rate': 25.40,
            'start_time': '09:00:00',
            'lunch_start': None,
            'end_time': '17:00:30',
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
                    'left': None,
                    'company_id': None,
                    'pay_rate': 25.40,
                    'start_time': '09:00:00',
                    'lunch_start': None,
                    'end_time': '17:00:30',
                    'caps_name': 'ALFRED',
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': 25.40,
                        'start_time': '09:00:00',
                        'lunch_start': None,
                        'end_time': '17:00:30',
                        'caps_name': 'ALFRED',
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
            'left':     None,
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
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': 'PUT ALFRED',
                },
            }
        )

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            sorted(json.loads(response.decode('utf-8'))['data'], key=lambda x: x['id']),
            [
                {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': '2015-11-01T09:30:12Z',
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': 'PUT ALFRED',
                },
                {
                    'id':   2,
                    'name': 'Bob',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            ]
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
            'name':     'Alfred',
            'joined':   '2015-11-01T09:30:12Z',
            'left':     None,
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
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': 'PATCH ALFRED',
                },
            }
        )

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            sorted(json.loads(response.decode('utf-8'))['data'], key=lambda x: x['id']),
            [
                {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': '2015-11-01T09:30:12Z',
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': 'PATCH ALFRED',
                },
                {
                    'id':   2,
                    'name': 'Bob',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            ]
        )

        body = json.dumps({
            'name': 'Jack',
            'joined': '2014-11-01T09:30:12Z',
        })
        response, = self.simulate_request('/employees/1', query_string='name=Bob', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertConflict(response, 'Resource found but conditions violated')

        response, = self.simulate_request('/employees/1', query_string='name=Alfred', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Jack',
                    'joined': '2014-11-01T09:30:12Z',
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': 'PATCH JACK',
                },
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                ]
            }
        )

    def test_single_delete_with_preconditions(self):
        now = datetime.now()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/employees/1', query_string='name=Bob', method='DELETE', headers={'Accept': 'application/json'})
        self.assertConflict(response, 'Resource found but conditions violated')

        response, = self.simulate_request('/employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Jim',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
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
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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

    def test_single_delete_violates_foreign_key(self):
        now = datetime.now()
        initech = Company(name="Initech")
        self.db_session.add(initech)
        self.db_session.add(Employee(name="Jim", joined=now, company=initech))
        self.db_session.add(Employee(name="Bob", joined=now))
        self.db_session.commit()

        response, = self.simulate_request('/companies/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '409 Conflict')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'title':        'Conflict',
                'description':  'Other content links to this',
            }
        )

        response, = self.simulate_request('/companies/1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Initech',
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
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': 1,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                ]
            }
        )

        # Now ensure the failed delete does not leave a transaction open
        body = json.dumps({
            'name': 'Alfred',
            'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })
        # Commits transaction:
        response, = self.simulate_request('/employees', method='POST', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '201 Created')

        body = json.dumps({
            'name': 'Bob',
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
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': 1,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Alfred',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': 'ALFRED',
                    },
                ]
            }
        )

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
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
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
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            }
        )

    def test_single_get_not_found(self):
        response = self.simulate_request('/employees/3', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)

    def test_subcollection(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(id=1, name="Jim", joined=now))
        self.db_session.add(Employee(id=2, name="Bob", joined=now))
        self.db_session.add(Employee(id=3, name="Jack", joined=now))
        self.db_session.add(Employee(id=4, name="Alice Joplin", joined=now))
        initech = Company(name="Initech")
        self.db_session.add(initech)
        self.db_session.add(Employee(id=5, name="Company Man", joined=now, company=initech))
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
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
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id__gt__gt=1', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response)

        response, = self.simulate_request('/employees', query_string='id__foo=1', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response)

        response, = self.simulate_request('/employees', query_string='id__gt=3', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   4,
                        'name': 'Alice Joplin',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   5,
                        'name': 'Company Man',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': initech.id,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id__gte=4', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   4,
                        'name': 'Alice Joplin',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   5,
                        'name': 'Company Man',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': initech.id,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id__lt=2', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='id__lte=1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='name__contains=J', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Jack',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   4,
                        'name': 'Alice Joplin',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='name__startswith=J', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Jack',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='foo=1', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response)

        response, = self.simulate_request('/employees', query_string='company=1', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response)

        response, = self.simulate_request('/companies', query_string='employees=1', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response)

        response, = self.simulate_request('/employees', query_string='company_id={0}'.format(initech.id), method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   5,
                        'name': 'Company Man',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': initech.id,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='company_id__null=1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Jack',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   4,
                        'name': 'Alice Joplin',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees', query_string='company_id__null=0', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   5,
                        'name': 'Company Man',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': initech.id,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    }
                ]
            }
        )


    def test_bad_route_filter(self):
        self.app.add_route('/bad-employees/{foo}/stuff', EmployeeCollectionResource(self.db_engine))
        self.app.add_route('/bad-employees/{foo}', EmployeeResource(self.db_engine))

        response, = self.simulate_request('/bad-employees/1/stuff', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/bad-employees/1/stuff', method='POST', body=json.dumps({}), headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/bad-employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/bad-employees/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/bad-employees/1', method='PUT', body=json.dumps({}), headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/bad-employees/1', method='PATCH', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertInternalServerError(response)

        self.app.add_route('/more-bad-employees/{company}/stuff', EmployeeCollectionResource(self.db_engine))
        self.app.add_route('/more-bad-employees/{company}', EmployeeResource(self.db_engine))

        response, = self.simulate_request('/more-bad-employees/1/stuff', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/more-bad-employees/1/stuff', method='POST', body='{}', headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/more-bad-employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/more-bad-employees/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/more-bad-employees/1', method='PUT', body=json.dumps({}), headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertInternalServerError(response)

        response, = self.simulate_request('/more-bad-employees/1', method='PATCH', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertInternalServerError(response)

    def test_mapping(self):
        now = datetime.utcnow()
        self.db_session.add(Employee(name="Jim", joined=now))
        self.db_session.commit()

        self.app.add_route('/other-employees/{employee_id}', OtherEmployeeResource(self.db_engine))

        response, = self.simulate_request('/other-employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Jim',
                    'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            }
        )

        body = json.dumps({
            'name': 'Alfred',
            'joined': '2015-11-01T09:30:12Z',
        })
        response, = self.simulate_request('/other-employees/1', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Alfred',
                    'joined': '2015-11-01T09:30:12Z',
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            }
        )

        body = json.dumps({
            'name': 'Bob',
            'joined': '2015-12-01T09:30:12Z',
        })
        response, = self.simulate_request('/other-employees/1', method='PUT', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': {
                    'id':   1,
                    'name': 'Bob',
                    'joined': '2015-12-01T09:30:12Z',
                    'left': None,
                    'company_id': None,
                    'pay_rate': None,
                    'start_time': None,
                    'lunch_start': None,
                    'end_time': None,
                    'caps_name': None,
                },
            }
        )

        response, = self.simulate_request('/employees/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {}
        )

        response = self.simulate_request('/other-employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '404 Not Found')
        self.assertEqual(response, [])

    def test_patch_collection(self):
        now = datetime.utcnow()
        body = json.dumps({
            'patches': [
                {'op': 'add', 'path': '/', 'value': {'name': 'Jim', 'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ')}},
                {'op': 'add', 'path': '/', 'value': {'name': 'Bob', 'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ')}},
            ]
        })
        response, = self.simulate_request('/employees', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                ]
            }
        )

        # Add more
        body = json.dumps({
            'patches': [
                {'op': 'add', 'path': '/', 'value': {'name': 'Jack', 'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ')}},
            ]
        })
        response, = self.simulate_request('/employees', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '200 OK')

        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Jack',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                ]
            }
        )

        body = json.dumps({
            'patches': [
                {'op': 'add', 'path': '/', 'value': {'name': 'Jill', 'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ')}},
                {'op': 'add', 'path': '/', 'value': {'name': 'Bob', 'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ')}},
            ]
        })
        response, = self.simulate_request('/employees', method='PATCH', body=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '409 Conflict')

        # Jill has not been added - last request failed atomically
        response, = self.simulate_request('/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertEqual(
            json.loads(response.decode('utf-8')),
            {
                'data': [
                    {
                        'id':   1,
                        'name': 'Jim',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   2,
                        'name': 'Bob',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                    {
                        'id':   3,
                        'name': 'Jack',
                        'joined': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'left': None,
                        'company_id': None,
                        'pay_rate': None,
                        'start_time': None,
                        'lunch_start': None,
                        'end_time': None,
                        'caps_name': None,
                    },
                ]
            }
        )
