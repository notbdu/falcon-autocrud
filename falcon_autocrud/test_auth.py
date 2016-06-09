from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from falcon.errors import HTTPUnauthorized, HTTPForbidden
import json
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, Numeric, String, Time


from .resource import CollectionResource, SingleResource
from falcon_autocrud.auth import identify, authorize


found_user = None

class TestIdentifier(object):
    def identify(self, req, resp, resource, params):
        global found_user
        found_user = req.get_header('Authorization')
        req.context['user'] = found_user
        if found_user is None:
            raise HTTPUnauthorized('Authentication Required', 'No credentials supplied', None)

class JimAuthorizer(object):
    def authorize(self, req, resp, resource, params):
        if 'user' not in req.context or req.context['user'] != 'Jim':
            raise HTTPForbidden('Permission Denied', 'User does not have access to this resource')

class BobAuthorizer(object):
    def authorize(self, req, resp, resource, params):
        if 'user' not in req.context or req.context['user'] != 'Bob':
            raise HTTPForbidden('Permission Denied', 'User does not have access to this resource')

@identify(TestIdentifier)
@authorize(JimAuthorizer)
class AccountCollectionResource(CollectionResource):
    model = Account

@identify(TestIdentifier)
@authorize(BobAuthorizer)
class AccountResource(SingleResource):
    model = Account

@identify(TestIdentifier)
@authorize(JimAuthorizer, methods=['GET', 'POST'])
@authorize(BobAuthorizer, methods=['PATCH'])
class OtherAccountCollectionResource(CollectionResource):
    model = Account

@identify(TestIdentifier)
@authorize(JimAuthorizer, methods=['GET', 'DELETE'])
@authorize(BobAuthorizer, methods=['PUT', 'PATCH'])
class OtherAccountResource(SingleResource):
    model = Account


class AuthTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))
        self.app.add_route('/other-accounts', OtherAccountCollectionResource(self.db_engine))
        self.app.add_route('/other-accounts/{id}', OtherAccountResource(self.db_engine))

    def test_no_identification(self):
        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json'})
        self.assertUnauthorized(response)
        self.assertEqual(found_user, None)
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertUnauthorized(response)
        self.assertEqual(found_user, None)

    def test_provided_identification(self):
        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertOK(response)
        self.assertEqual(found_user, 'Jim')
        response = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertNotFound(response)
        self.assertEqual(found_user, 'Bob')

    def test_authorization_checks(self):
        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertForbidden(response)
        response, = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertForbidden(response)

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertOK(response)
        response = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertNotFound(response)

    def test_authorization_by_method(self):
        response, = self.simulate_request('/other-accounts', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertOK(response)
        response, = self.simulate_request('/other-accounts', method='POST', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Jim'})
        self.assertCreated(response)
        response, = self.simulate_request('/other-accounts', method='PATCH', body=json.dumps({'patches': []}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Jim'})
        self.assertForbidden(response)

        response, = self.simulate_request('/other-accounts/1', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertOK(response)
        response, = self.simulate_request('/other-accounts/1', method='PUT', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Jim'})
        self.assertForbidden(response)
        response, = self.simulate_request('/other-accounts/1', method='PATCH', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Jim'})
        self.assertForbidden(response)

        response, = self.simulate_request('/other-accounts', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertForbidden(response)
        response, = self.simulate_request('/other-accounts', method='POST', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bob'})
        self.assertForbidden(response)
        response, = self.simulate_request('/other-accounts', method='PATCH', body=json.dumps({'patches': []}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bob'})
        self.assertOK(response)

        response, = self.simulate_request('/other-accounts/1', method='GET', headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertForbidden(response)
        response, = self.simulate_request('/other-accounts/1', method='PUT', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bob'})
        self.assertOK(response)
        response, = self.simulate_request('/other-accounts/1', method='PATCH', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bob'})
        self.assertOK(response)
        response, = self.simulate_request('/other-accounts/1', method='DELETE', body=json.dumps({}), headers={'Accept': 'application/json', 'Authorization': 'Bob'})
        self.assertForbidden(response)

        response, = self.simulate_request('/other-accounts/1', method='DELETE', body=json.dumps({}), headers={'Accept': 'application/json', 'Authorization': 'Jim'})
        self.assertOK(response)
