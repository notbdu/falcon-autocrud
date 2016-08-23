import json
from sqlalchemy import Column, Integer, String

from .test_base import Base, BaseTestCase

from .resource import CollectionResource, SingleResource

class Character(Base):
    __tablename__ = 'characters'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50))


class CharacterCollectionResource(CollectionResource):
    model = Character

class DefaultSortCharacterCollectionResource(CollectionResource):
    model = Character
    default_sort = ['name', '-id']

class InvalidDefaultSortCharacterCollectionResource(CollectionResource):
    model = Character
    default_sort = ['name', 'xid']


class SortTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/characters', CharacterCollectionResource(self.db_engine))
        self.app.add_route('/default-sort-characters', DefaultSortCharacterCollectionResource(self.db_engine))
        self.app.add_route('/invalid-default-sort-characters', InvalidDefaultSortCharacterCollectionResource(self.db_engine))

    def create_common_fixtures(self):
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 1, 'name': 'John'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 2, 'name': 'Barry'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 3, 'name': 'Thea'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 4, 'name': 'Laurel'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 5, 'name': 'Felicity'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 6, 'name': 'Oliver'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 7, 'name': 'Roy'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 8, 'name': 'Iris'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 9, 'name': 'Caitlin'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 10, 'name': 'Cisco'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 11, 'name': 'Cisco'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        response, = self.simulate_request('/characters', method='POST', body=json.dumps({'id': 12, 'name': 'Cisco'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})


    def test_unsorted(self):
        response, = self.simulate_request('/characters', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 1, 'name': 'John'},
                {'id': 2, 'name': 'Barry'},
                {'id': 3, 'name': 'Thea'},
                {'id': 4, 'name': 'Laurel'},
                {'id': 5, 'name': 'Felicity'},
                {'id': 6, 'name': 'Oliver'},
                {'id': 7, 'name': 'Roy'},
                {'id': 8, 'name': 'Iris'},
                {'id': 9, 'name': 'Caitlin'},
                {'id': 10, 'name': 'Cisco'},
                {'id': 11, 'name': 'Cisco'},
                {'id': 12, 'name': 'Cisco'},
            ]
        })

    def test_default_sort(self):
        response, = self.simulate_request('/default-sort-characters', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 2, 'name': 'Barry'},
                {'id': 9, 'name': 'Caitlin'},
                {'id': 12, 'name': 'Cisco'},
                {'id': 11, 'name': 'Cisco'},
                {'id': 10, 'name': 'Cisco'},
                {'id': 5, 'name': 'Felicity'},
                {'id': 8, 'name': 'Iris'},
                {'id': 1, 'name': 'John'},
                {'id': 4, 'name': 'Laurel'},
                {'id': 6, 'name': 'Oliver'},
                {'id': 7, 'name': 'Roy'},
                {'id': 3, 'name': 'Thea'},
            ]
        })

    def test_invalid_default_sort(self):
        response, = self.simulate_request('/invalid-default-sort-characters', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)