import falcon
import json

from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from .resource import CollectionResource, SingleResource


class AccountCollectionResource(CollectionResource):
    model = Account

class AccountResource(SingleResource):
    model = Account

    def modify_patch(self, req, resp, resource, *args, **kwargs):
        resource.name = resource.name + 'arino'

class MethodTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))

    def create_common_fixtures(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'John'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

    def test_modify(self):
        response, = self.simulate_request('/accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Sam'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':       1,
                'name':     'Samarino',
                'owner':    None,
            }
        })
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':       1,
                'name':     'Samarino',
                'owner':    None,
            }
        })

        response, = self.simulate_request('/accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':       1,
                'name':     'Bobarino',
                'owner':    None,
            }
        })
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':       1,
                'name':     'Bobarino',
                'owner':    None,
            }
        })
