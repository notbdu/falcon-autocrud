import falcon
import json

from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from .resource import CollectionResource, SingleResource


class AccountCollectionResource(CollectionResource):
    model = Account

class AccountResource(SingleResource):
    model = Account

proof = {}
count = 0

class AfterAccountCollectionResource(CollectionResource):
    model = Account

    def after_get(self, req, resp, collection, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'found': len(list(collection)), 'found2': len(req.context['result']['data']), 'status': resp.status}

    def after_post(self, req, resp, new, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'name': new.name, 'id': req.context['result']['data']['id'], 'status': resp.status}

    def after_patch(self, req, resp, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'status': resp.status}


class AfterAccountResource(SingleResource):
    model = Account

    def after_get(self, req, resp, item, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'name': item.name, 'id': req.context['result']['data']['id'], 'status': resp.status}

    def after_put(self, req, resp, item, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'name': item.name, 'id': req.context['result']['data']['id'], 'status': resp.status}

    def after_patch(self, req, resp, item, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'name': item.name, 'id': req.context['result']['data']['id'], 'status': resp.status}

    def after_delete(self, req, resp, item, *args, **kwargs):
        global proof
        global count
        count += 1
        proof = {'count': count, 'name': item.name, 'status': resp.status}



class MethodTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))
        self.app.add_route('/after-accounts', AfterAccountCollectionResource(self.db_engine))
        self.app.add_route('/after-accounts/{id}', AfterAccountResource(self.db_engine))

    def test_no_after(self):
        proof = {}

        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts', method='PATCH', body=json.dumps({'patches': [{'op': 'add', 'path': '/', 'value': {'id': 2, 'name': 'Jim'}}]}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts/1', method='PUT', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts/1', method='PATCH', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

        response, = self.simulate_request('/accounts/1', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {})

    def test_after(self):
        global proof
        proof = {}

        response, = self.simulate_request('/after-accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 1, 'name': 'Bob', 'id': 1, 'status': falcon.HTTP_CREATED})

        proof = {}
        response, = self.simulate_request('/after-accounts', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 2, 'found': 1, 'found2': 1, 'status': falcon.HTTP_OK})

        proof = {}
        response, = self.simulate_request('/after-accounts', method='PATCH', body=json.dumps({'patches': [{'op': 'add', 'path': '/', 'value': {'id': 2, 'name': 'Jim'}}]}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 3, 'status': falcon.HTTP_OK})

        proof = {}
        response, = self.simulate_request('/after-accounts/1', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 4, 'name': 'Bob', 'id': 1, 'status': falcon.HTTP_OK})

        proof = {}
        response, = self.simulate_request('/after-accounts/1', method='PUT', body=json.dumps({'id': 1, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 5, 'name': 'Jack', 'id': 1, 'status': falcon.HTTP_OK})

        proof = {}
        response, = self.simulate_request('/after-accounts/1', method='PATCH', body=json.dumps({'id': 1, 'name': 'Sam'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 6, 'name': 'Sam', 'id': 1, 'status': falcon.HTTP_OK})

        proof = {}
        response, = self.simulate_request('/after-accounts/1', method='DELETE', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(proof, {'count': 7, 'name': 'Sam', 'status': falcon.HTTP_OK})
