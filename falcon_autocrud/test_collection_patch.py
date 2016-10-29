from .test_base import Base, BaseTestCase
from .test_fixtures import Account, Company

from datetime import datetime
from falcon.errors import HTTPUnauthorized, HTTPForbidden
import json
from sqlalchemy import Column, DateTime


from .resource import CollectionResource, SingleResource

class RootResource(CollectionResource):
    methods     = ['PATCH']
    patch_paths = {
        '/accounts':    Account,
        '/companies':   Company,
    }

class AccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['PATCH']


class CollectionPatchTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/', RootResource(self.db_engine))
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))

    def test_paths_patch(self):
        patches = {
            'patches': [
                {'op': 'add', 'path': '/accounts', 'value': {'id': 1, 'name': 'Initech Sales', 'owner': 'Jim'}},
                {'op': 'add', 'path': '/accounts', 'value': {'id': 2, 'name': 'ACME Sales', 'owner': 'Bob'}},
                {'op': 'add', 'path': '/companies', 'value': {'id': 11, 'name': 'Initech'}},
                {'op': 'add', 'path': '/companies', 'value': {'id': 12, 'name': 'ACME'}},
                {'op': 'add', 'path': '/companies', 'value': {'id': 13, 'name': 'BigCorp'}},
            ]
        }
        response, = self.simulate_request('/', method='PATCH', body=json.dumps(patches), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        accounts    = self.db_session.query(Account).order_by(Account.name).all()
        companies   = self.db_session.query(Company).order_by(Company.name).all()

        self.assertEqual(
            [{
                'id':       account.id,
                'name':     account.name,
                'owner':    account.owner,
            } for account in accounts],
            [{
                'id':       2,
                'name':     'ACME Sales',
                'owner':    'Bob',
            }, {
                'id':       1,
                'name':     'Initech Sales',
                'owner':    'Jim',
            }],
        )
        self.assertEqual(
            [{
                'id':       company.id,
                'name':     company.name,
            } for company in companies],
            [{
                'id':       12,
                'name':     'ACME',
            }, {
                'id':       13,
                'name':     'BigCorp',
            }, {
                'id':       11,
                'name':     'Initech',
            }],
        )

    def test_root_patch(self):
        patches = {
            'patches': [
                {'op': 'add', 'path': '/', 'value': {'id': 1, 'name': 'Initech Sales', 'owner': 'Jim'}},
                {'op': 'add', 'path': '/', 'value': {'id': 2, 'name': 'ACME Sales', 'owner': 'Bob'}},
            ]
        }
        response, = self.simulate_request('/accounts', method='PATCH', body=json.dumps(patches), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        accounts = self.db_session.query(Account).order_by(Account.name).all()

        self.assertEqual(
            [{'id': account.id, 'name': account.name, 'owner': account.owner} for account in accounts],
            [
                {'id': 2, 'name': 'ACME Sales', 'owner': 'Bob'},
                {'id': 1, 'name': 'Initech Sales', 'owner': 'Jim'},
            ],
        )
