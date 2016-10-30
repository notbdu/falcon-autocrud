import json

from .test_base import BaseTestCase
from .test_fixtures import Company, Employee

from .resource import CollectionResource

class CompanyCollectionResource(CollectionResource):
    model = Company
    methods = ['POST']

class EmployeeCollectionResource(CollectionResource):
    model = Employee
    methods = ['POST']


class SubresourceTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/companies', CompanyCollectionResource(self.db_engine))
        self.app.add_route('/employees', EmployeeCollectionResource(self.db_engine))

    def test_one_to_many(self):
        post = {
            'name':         'Initech',
            'employees':    [
                {
                    'name':     'Bob',
                    'joined':   '2016-10-01T00:00:00Z'
                },
                {
                    'name':     'Jim',
                    'joined':   '2016-10-02T00:00:00Z'
                }
            ]
        }
        response, = self.simulate_request('/companies', method='POST', body=json.dumps(post), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id': 1,
                'name': 'Initech',
            }
        })

        company = self.db_session.query(Company).filter(Company.id == 1).one_or_none()
        self.assertTrue(company is not None)
        self.assertEqual(company.name, 'Initech')

        self.assertEqual([employee.name for employee in sorted(company.employees, key=lambda emp: emp.name)], ['Bob', 'Jim'])

        employees = self.db_session.query(Employee).filter(Employee.company_id == 1).order_by(Employee.name)
        self.assertEqual([employee.name for employee in employees], ['Bob', 'Jim'])
        self.assertEqual([employee.company.name for employee in employees], ['Initech', 'Initech'])

    def test_many_to_one(self):
        post = {
            'name':     'Alice',
            'joined':   '2016-10-01T00:00:00Z',
            'company':  {
                'name': 'BigCorp'
            },
        }
        response, = self.simulate_request('/employees', method='POST', body=json.dumps(post), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':           1,
                'name':         'Alice',
                'company_id':   1,
                'caps_name':    None,
                'joined':       '2016-10-01T00:00:00Z',
                'left':         None,
                'start_time':   None,
                'end_time':     None,
                'lunch_start':  None,
                'pay_rate':     None,
            }
        })

        employee = self.db_session.query(Employee).filter(Employee.id == 1).one_or_none()
        self.assertTrue(employee is not None)
        self.assertEqual(employee.name, 'Alice')

        self.assertEqual(employee.company.name, 'BigCorp')

        company = self.db_session.query(Company).filter(Company.id == 1).one_or_none()
        self.assertTrue(company is not None)
        self.assertEqual(company.name, 'BigCorp')
        self.assertEqual([employee.name for employee in company.employees], ['Alice'])
