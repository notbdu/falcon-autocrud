from .test_base import BaseTestCase

from .resource import CollectionResource, SingleResource
from .test_fixtures import Company, Employee


class EmployeeCollectionResource(CollectionResource):
    model = Employee

    def get_filter(self, req, resp, query, *args, **kwargs):
        if 'company_name' in req.params:
            company_name = req.params['company_name']
            del req.params['company_name']
            query = query.join(Employee.company).filter(Company.name == company_name)
        return query

class EmployeeResource(SingleResource):
    model = Employee
    allowed_included = {
        'companies': {
            'link': lambda resource: [resource.company],
        }
    }

class LimitedLinkEmployeeResource(SingleResource):
    model = Employee
    allowed_included = {
        'companies': {
            'link':             lambda resource: [resource.company],
            'response_fields':  ['name'],
        }
    }

class CompanyEmployeeCollectionResource(CollectionResource):
    model = Employee

    attr_map = {
        'company_id':   lambda req, resp, query, *args, **kwargs: query.join(Employee.company).filter(Company.id == kwargs['company_id'])
    }

class CompanyEmployeeResource(SingleResource):
    model = Employee

    attr_map = {
        'company_id':   lambda req, resp, query, *args, **kwargs: query.join(Employee.company).filter(Company.id == kwargs['company_id'])
    }


class PreconditionTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/employees', EmployeeCollectionResource(self.db_engine))
        self.app.add_route('/employees/{id}', EmployeeResource(self.db_engine))
        self.app.add_route('/employees2/{id}', LimitedLinkEmployeeResource(self.db_engine))
        self.app.add_route('/companies/{company_id}/employees', CompanyEmployeeCollectionResource(self.db_engine))
        self.app.add_route('/companies/{company_id}/employees/{id}', CompanyEmployeeResource(self.db_engine))

    def create_common_fixtures(self):
        self.db_session.add(Company(id=1, name="Initech"))
        self.db_session.add(Company(id=2, name="Parrots R Us"))
        self.db_session.add(Employee(id=1, name="Jim", company_id=1))
        self.db_session.add(Employee(id=2, name="Bob", company_id=1))
        self.db_session.add(Employee(id=3, name="Jack", company_id=2))
        self.db_session.add(Employee(id=4, name="Alice", company_id=2))
        self.db_session.add(Employee(id=5, name="Jane", company_id=1))
        self.db_session.commit()

    def test_collection_get_filter(self):
        response, = self.simulate_request('/employees', query_string='company_name=Parrots%20R%20Us', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
               "data" : [
                  {
                     "id":          3,
                     "company_id":  2,
                     "name":        "Jack",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
                  {
                     "id":          4,
                     "company_id":  2,
                     "name":        "Alice",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
               ]
            }
        )

    def test_invalid_included(self):
        response, = self.simulate_request('/employees/1', method='GET', query_string='__included=nonexistent', headers={'Accept': 'application/json'})
        self.assertBadRequest(response, 'Invalid parameter', 'The "__included" parameter includes invalid entities')

    def test_included(self):
        response, = self.simulate_request('/employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
                "data" : {
                    "id":          1,
                    "company_id":  1,
                    "name":        "Jim",
                    "caps_name":   None,
                    "end_time":    None,
                    "joined":      None,
                    "left":        None,
                    "lunch_start": None,
                    "pay_rate":    None,
                    "start_time":  None,
                },
            }
        )

        response, = self.simulate_request('/employees/1', method='GET', query_string='__included=companies', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
                "data" : {
                    "id":          1,
                    "company_id":  1,
                    "name":        "Jim",
                    "caps_name":   None,
                    "end_time":    None,
                    "joined":      None,
                    "left":        None,
                    "lunch_start": None,
                    "pay_rate":    None,
                    "start_time":  None,
                },
                "included": [
                    {
                        "id":           1,
                        "type":         "companies",
                        "attributes":   {
                            "id":   1,
                            "name": "Initech",
                        },
                    }
                ]
            }
        )

        response, = self.simulate_request('/employees2/1', method='GET', query_string='__included=companies', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
                "data" : {
                    "id":          1,
                    "company_id":  1,
                    "name":        "Jim",
                    "caps_name":   None,
                    "end_time":    None,
                    "joined":      None,
                    "left":        None,
                    "lunch_start": None,
                    "pay_rate":    None,
                    "start_time":  None,
                },
                "included": [
                    {
                        "id":           1,
                        "type":         "companies",
                        "attributes":   {
                            "name": "Initech",
                        },
                    }
                ]
            }
        )

    def test_collection_attr_map(self):
        response, = self.simulate_request('/companies/1/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
               "data" : [
                  {
                     "id":          1,
                     "company_id":  1,
                     "name":        "Jim",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
                  {
                     "id":          2,
                     "company_id":  1,
                     "name":        "Bob",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
                  {
                     "id":          5,
                     "company_id":  1,
                     "name":        "Jane",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  }
               ]
            }
        )

        response, = self.simulate_request('/companies/2/employees', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
               "data" : [
                  {
                     "id":          3,
                     "company_id":  2,
                     "name":        "Jack",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
                  {
                     "id":          4,
                     "company_id":  2,
                     "name":        "Alice",
                     "caps_name":   None,
                     "end_time":    None,
                     "joined":      None,
                     "left":        None,
                     "lunch_start": None,
                     "pay_rate":    None,
                     "start_time":  None,
                  },
               ]
            }
        )

        response, = self.simulate_request('/companies/1/employees/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
                "data" : {
                    "id":          1,
                    "company_id":  1,
                    "name":        "Jim",
                    "caps_name":   None,
                    "end_time":    None,
                    "joined":      None,
                    "left":        None,
                    "lunch_start": None,
                    "pay_rate":    None,
                    "start_time":  None,
                }
            }
        )
        response, = self.simulate_request('/companies/2/employees/3', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(
            response,
            {
                "data" : {
                    "id":          3,
                    "company_id":  2,
                    "name":        "Jack",
                    "caps_name":   None,
                    "end_time":    None,
                    "joined":      None,
                    "left":        None,
                    "lunch_start": None,
                    "pay_rate":    None,
                    "start_time":  None,
                }
            }
        )

        response = self.simulate_request('/companies/1/employees/3', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)
