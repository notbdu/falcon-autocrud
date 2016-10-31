import json
from sqlalchemy import Column, Integer, String

from .test_base import Base, BaseTestCase
from .test_fixtures import Character

from .resource import CollectionResource, SingleResource

class CharacterCollectionResource(CollectionResource):
    model = Character

class CharacterResource(SingleResource):
    model = Character


class SortTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/characters', CharacterCollectionResource(self.db_engine))
        self.app.add_route('/characters/{id}', CharacterResource(self.db_engine))

    def test_post(self):
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 1, 'indirect_name': 'Barry'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id': 1,
                'name': 'Barry',
                'team_id': None,
            }
        })

    def test_put(self):
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 1, 'indirect_name': 'Barry'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters/1', method='PUT', body=json.dumps({'id': 1, 'indirect_name': 'Flash'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id': 1,
                'name': 'Flash',
                'team_id': None,
            }
        })

    def test_patch(self):
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 1, 'indirect_name': 'Barry'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters/1', method='PATCH', body=json.dumps({'indirect_name': 'Flash'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id': 1,
                'name': 'Flash',
                'team_id': None,
            }
        })
