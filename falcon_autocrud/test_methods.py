import json

from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from .resource import CollectionResource, SingleResource


class AccountCollectionResource(CollectionResource):
    model = Account
    default_sort = ['id']

class AccountResource(SingleResource):
    model = Account

class GetOnlyAccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['GET']

class GetOnlyAccountResource(SingleResource):
    model   = Account
    methods = ['GET']

class PostOnlyAccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['POST']

class PostOnlyAccountResource(SingleResource):
    model   = Account
    methods = ['POST']

class PutOnlyAccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['PUT']

class PutOnlyAccountResource(SingleResource):
    model   = Account
    methods = ['PUT']

class PatchOnlyAccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['PATCH']

class PatchOnlyAccountResource(SingleResource):
    model   = Account
    methods = ['PATCH']

class DeleteOnlyAccountCollectionResource(CollectionResource):
    model   = Account
    methods = ['DELETE']

class DeleteOnlyAccountResource(SingleResource):
    model   = Account
    methods = ['DELETE']


class MethodTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))
        self.app.add_route('/getonly-accounts', GetOnlyAccountCollectionResource(self.db_engine))
        self.app.add_route('/getonly-accounts/{id}', GetOnlyAccountResource(self.db_engine))
        self.app.add_route('/postonly-accounts', PostOnlyAccountCollectionResource(self.db_engine))
        self.app.add_route('/postonly-accounts/{id}', PostOnlyAccountResource(self.db_engine))
        self.app.add_route('/putonly-accounts', PutOnlyAccountCollectionResource(self.db_engine))
        self.app.add_route('/putonly-accounts/{id}', PutOnlyAccountResource(self.db_engine))
        self.app.add_route('/patchonly-accounts', PatchOnlyAccountCollectionResource(self.db_engine))
        self.app.add_route('/patchonly-accounts/{id}', PatchOnlyAccountResource(self.db_engine))
        self.app.add_route('/deleteonly-accounts', DeleteOnlyAccountCollectionResource(self.db_engine))
        self.app.add_route('/deleteonly-accounts/{id}', DeleteOnlyAccountResource(self.db_engine))

    def test_get(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 1, 'name': 'Bob', 'owner': None}]})
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Bob', 'owner': None}})

        response, = self.simulate_request('/getonly-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 1, 'name': 'Bob', 'owner': None}]})
        response, = self.simulate_request('/getonly-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Bob', 'owner': None}})

        response = self.simulate_request('/postonly-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)

        response = self.simulate_request('/putonly-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)

        response = self.simulate_request('/patchonly-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)

        response = self.simulate_request('/deleteonly-accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertMethodNotAllowed(response)

    def test_post(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)
        response = self.simulate_request('/accounts/1', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/getonly-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/getonly-accounts/1', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response, = self.simulate_request('/postonly-accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)
        response = self.simulate_request('/postonly-accounts/1', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts/1', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts/1', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts/1', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 1, 'name': 'Bob', 'owner': None}, {'id': 2, 'name': 'Jim', 'owner': None}]})
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Bob', 'owner': None}})

    def test_put(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response = self.simulate_request('/accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Jim', 'owner': None}})

        response = self.simulate_request('/getonly-accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/getonly-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)
        response = self.simulate_request('/patchonly-accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)

        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Jack', 'owner': None}})

    def test_patch(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response = self.simulate_request('/accounts', method='PATCH', body=json.dumps({'patches': [{'op': 'add', 'path': '/', 'value': {'id': 2, 'name': 'Jane'}}]}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 1, 'name': 'Bob', 'owner': None}, {'id': 2, 'name': 'Jane', 'owner': None}]})

        response = self.simulate_request('/accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': {'id': 1, 'name': 'Jim', 'owner': None}})

        response = self.simulate_request('/getonly-accounts', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/getonly-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts', method='PATCH', body=json.dumps({'patches': [{'op': 'add', 'path': '/', 'value': {'id': 3, 'name': 'Dan'}}]}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)
        response = self.simulate_request('/patchonly-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)
        response = self.simulate_request('/deleteonly-accounts', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Alice'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 1, 'name': 'Jack', 'owner': None}, {'id': 2, 'name': 'Jane', 'owner': None}, {'id': 3, 'name': 'Dan', 'owner': None}]})

    def test_delete(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response)

        response = self.simulate_request('/accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/accounts/1', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 2, 'name': 'Jim', 'owner': None}]})

        response = self.simulate_request('/getonly-accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/getonly-accounts/2', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/postonly-accounts/2', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/putonly-accounts/2', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/patchonly-accounts/2', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)
        response = self.simulate_request('/deleteonly-accounts', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertMethodNotAllowed(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': [{'id': 2, 'name': 'Jim', 'owner': None}]})

        response = self.simulate_request('/deleteonly-accounts/2', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {'data': []})
