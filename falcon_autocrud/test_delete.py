from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from datetime import datetime
from falcon.errors import HTTPUnauthorized, HTTPForbidden
import json
from sqlalchemy import Column, DateTime


from .resource import CollectionResource, SingleResource

class DeletableAccount(Account):
    deleted = Column(DateTime, unique=True)

class AccountCollectionResource(CollectionResource):
    model = DeletableAccount
    default_sort = ['id']

class AccountResource(SingleResource):
    model = DeletableAccount

class AltAccountCollectionResource(CollectionResource):
    model = DeletableAccount

    def get_filter(self, req, resp, resources, *args, **kwargs):
        return resources.filter(DeletableAccount.deleted == None)

class AltAccountResource(SingleResource):
    model = DeletableAccount

    def get_filter(self, req, resp, resources, *args, **kwargs):
        return resources.filter(DeletableAccount.deleted == None)

    def mark_deleted(self, req, resp, instance, *args, **kwargs):
        instance.deleted = datetime.utcnow()

class DeleteTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))
        self.app.add_route('/alt-accounts', AltAccountCollectionResource(self.db_engine))
        self.app.add_route('/alt-accounts/{id}', AltAccountResource(self.db_engine))

    def test_standard_delete(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response, = self.simulate_request('/accounts/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertOK(response)

        response = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)
        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [
            {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
                'deleted':  None,
            }
        ]})

    def test_modified_delete(self):
        response, = self.simulate_request('/alt-accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)
        response, = self.simulate_request('/alt-accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response, = self.simulate_request('/alt-accounts/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertOK(response)

        response = self.simulate_request('/alt-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)
        response, = self.simulate_request('/alt-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [
            {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
                'deleted':  None,
            }
        ]})
        # Can't even query on deleted field with filter in place
        response, = self.simulate_request('/alt-accounts', query_string='deleted__null=1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [
            {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
                'deleted':  None,
            }
        ]})
        # But "deleted" entry is still in DB, just marked as deleted...
        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        deleted = json.loads(response.decode('utf-8'))['data'][0]['deleted']
        self.assertOK(response, {'data': [
            {
                'id':       1,
                'name':     'Bob',
                'owner':    None,
                'deleted':  deleted,
            },
            {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
                'deleted':  None,
            }
        ]})
