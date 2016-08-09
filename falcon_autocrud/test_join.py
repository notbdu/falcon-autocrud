from .test_base import BaseTestCase

from .resource import CollectionResource
from .test_fixtures import Company, Employee


class EmployeeCollectionResource(CollectionResource):
    model = Employee

    def get_filter(self, req, resp, query, *args, **kwargs):
        if 'company_name' in req.params:
            company_name = req.params['company_name']
            del req.params['company_name']
            query = query.join(Employee.company).filter(Company.name == company_name)
        return query


class PreconditionTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/employees', EmployeeCollectionResource(self.db_engine))

    def test_collection_get_filter(self):
        self.db_session.add(Company(id=1, name="Initech"))
        self.db_session.add(Company(id=2, name="Parrots R Us"))
        self.db_session.add(Employee(id=1, name="Jim", company_id=1))
        self.db_session.add(Employee(id=2, name="Bob", company_id=1))
        self.db_session.add(Employee(id=3, name="Jack", company_id=2))
        self.db_session.add(Employee(id=4, name="Alice", company_id=2))
        self.db_session.add(Employee(id=5, name="Jane", company_id=1))
        self.db_session.commit()

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
                  }
               ]
            }
        )

