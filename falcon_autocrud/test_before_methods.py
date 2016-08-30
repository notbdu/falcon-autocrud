import falcon
import falcon.errors
import json

from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from .resource import CollectionResource, SingleResource


class AccountCollectionResource(CollectionResource):
    model = Account

class BeforeAccountCollectionResource(CollectionResource):
    model = Account

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        if resource.name == 'Jack':
            raise falcon.errors.HTTPForbidden('Permission Denied', 'Jack is not allowed')
        extra_resource = Account(id=req.context['doc']['id'] + 10, name=req.context['doc']['name'] + ' 2')
        db_session.add(extra_resource)

class MethodTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/before-accounts', BeforeAccountCollectionResource(self.db_engine))

    def test_no_before(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       1,
                'name':     'Bob',
                'owner':    None,
            }
        })

    def test_before(self):
        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       1,
                'name':     'Bob',
                'owner':    None,
            }
        })

        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
            }
        })

        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertForbidden(response, 'Jack is not allowed')

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 1, 'name': 'Bob', 'owner': None},
                {'id': 2, 'name': 'Jim', 'owner': None},
                {'id': 11, 'name': 'Bob 2', 'owner': None},
                {'id': 12, 'name': 'Jim 2', 'owner': None},
            ]
        })
