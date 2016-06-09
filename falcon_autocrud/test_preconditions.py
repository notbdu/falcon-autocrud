from .test_base import Base, BaseTestCase
from .test_fixtures import Account

from falcon.errors import HTTPUnauthorized, HTTPForbidden
import json

from .resource import CollectionResource, SingleResource


class AccountCollectionResource(CollectionResource):
    model = Account

class AccountResource(SingleResource):
    model = Account

    def delete_precondition(self, req, resp, query, *args, **kwargs):
        # Only allow deletes of non-owned accounts
        return query.filter(Account.owner == None)


class PreconditionTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/accounts/{id}', AccountResource(self.db_engine))

    def test_delete_precondition(self):
        self.db_session.add(Account(id=1, name="Foo", owner=None))
        self.db_session.add(Account(id=2, name="Bar", owner="Don Draper"))
        self.db_session.commit()

        response, = self.simulate_request('/accounts/1', method='DELETE', headers={'Accept': 'application/json'})
        self.assertOK(response)

        response = self.simulate_request('/accounts/1', method='GET', headers={'Accept': 'application/json'})
        self.assertNotFound(response)

        response, = self.simulate_request('/accounts/2', method='DELETE', headers={'Accept': 'application/json'})
        self.assertConflict(response, 'Resource found but conditions violated')

        response, = self.simulate_request('/accounts/2', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response)
