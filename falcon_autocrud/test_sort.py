import json
from sqlalchemy import Column, Integer, String

from .test_base import Base, BaseTestCase
from .test_fixtures import Character

from .resource import CollectionResource, SingleResource


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
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
            ]
        })

    def test_default_sort(self):
        response, = self.simulate_request('/default-sort-characters', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 2, 'name': 'Barry', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 3, 'name': 'Thea', 'team_id': None},
            ]
        })

    def test_invalid_default_sort(self):
        response, = self.simulate_request('/invalid-default-sort-characters', method='GET', headers={'Accept': 'application/json'})
        self.assertInternalServerError(response)

    def test_user_defined_sort(self):
        response, = self.simulate_request('/characters', query_string='__sort=-name,id', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
            ]
        })

    def test_single_user_defined_sort(self):
        response, = self.simulate_request('/characters', query_string='__sort=id', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
            ]
        })

        response, = self.simulate_request('/characters', query_string='__sort=-id', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
            ]
        })

    def test_user_defined_sort_overrides_default(self):
        response, = self.simulate_request('/default-sort-characters', query_string='__sort=-name,id', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
            ]
        })

    def test_invalid_sort(self):
        response, = self.simulate_request('/characters', query_string='__sort=-name,id,foo', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response, description='An attribute provided for sorting is invalid')

    def test_paging(self):
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=0&__limit=5', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 3, 'name': 'Thea', 'team_id': None},
                {'id': 7, 'name': 'Roy', 'team_id': None},
                {'id': 6, 'name': 'Oliver', 'team_id': None},
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
            ],
            'meta': {
                'offset':   0,
                'limit':    5,
                'total':    12,
            }
        })
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=5&__limit=5', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
            ],
            'meta': {
                'offset':   5,
                'limit':    5,
                'total':    12,
            }
        })
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=10&__limit=5', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
            ],
            'meta': {
                'offset':   10,
                'limit':    5,
                'total':    12,
            }
        })

    def test_paging_any_position(self):
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=3&__limit=8', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 4, 'name': 'Laurel', 'team_id': None},
                {'id': 1, 'name': 'John', 'team_id': None},
                {'id': 8, 'name': 'Iris', 'team_id': None},
                {'id': 5, 'name': 'Felicity', 'team_id': None},
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
            ],
            'meta': {
                'offset':   3,
                'limit':    8,
                'total':    12,
            }
        })
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=7&__limit=3', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
            ],
            'meta': {
                'offset':   7,
                'limit':    3,
                'total':    12,
            }
        })
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=7', method='GET', headers={'Accept': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 10, 'name': 'Cisco', 'team_id': None},
                {'id': 11, 'name': 'Cisco', 'team_id': None},
                {'id': 12, 'name': 'Cisco', 'team_id': None},
                {'id': 9, 'name': 'Caitlin', 'team_id': None},
                {'id': 2, 'name': 'Barry', 'team_id': None},
            ],
            'meta': {
                'offset':   7,
                'total':    12,
            }
        })

    def test_paging_types(self):
        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__offset=abc', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response, title='Invalid parameter', description='The "__offset" parameter is invalid. The value must be an integer.')

        response, = self.simulate_request('/characters', query_string='__sort=-name,id&__limit=abc', method='GET', headers={'Accept': 'application/json'})
        self.assertBadRequest(response, title='Invalid parameter', description='The "__limit" parameter is invalid. The value must be an integer.')
