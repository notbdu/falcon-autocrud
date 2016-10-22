import json
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
import os
import uuid

from .test_base import Base, BaseTestCase

from .resource import CollectionResource, SingleResource


if 'AUTOCRUD_DSN' in os.environ and os.environ['AUTOCRUD_DSN'].startswith('postgresql+pg8000:'):
    class Animal(Base):
        __tablename__ = 'animals'
        id          = Column(UUID(), primary_key=True)
        name        = Column(String(50), unique=True)

    class AnimalCollectionResource(CollectionResource):
        model = Animal

    class AnimalResource(SingleResource):
        model = Animal

    class SerializeTest(BaseTestCase):
        def create_test_resources(self):
            self.app.add_route('/animals', AnimalCollectionResource(self.db_engine))
            self.app.add_route('/animals/{id}', AnimalResource(self.db_engine))

        def test_uuid(self):
            id = uuid.uuid4().hex
            response, = self.simulate_request('/animals', method='POST', body=json.dumps({'id': id, 'name': 'Cat'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertCreated(response, {
                'data': {
                    'id': id,
                    'name': 'Cat',
                }
            })

            response, = self.simulate_request('/animals/{}'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': {
                    'id': id,
                    'name': 'Cat',
                }
            })
            response, = self.simulate_request('/animals'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': [{
                    'id': id,
                    'name': 'Cat',
                }]
            })

            response, = self.simulate_request('/animals/{}'.format(id), method='PATCH', body=json.dumps({'id': id, 'name': 'Dog'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': {
                    'id': id,
                    'name': 'Dog',
                }
            })

            response, = self.simulate_request('/animals/{}'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': {
                    'id': id,
                    'name': 'Dog',
                }
            })
            response, = self.simulate_request('/animals'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': [{
                    'id': id,
                    'name': 'Dog',
                }]
            })

            response, = self.simulate_request('/animals/{}'.format(id), method='PUT', body=json.dumps({'id': id, 'name': 'Cow'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': {
                    'id': id,
                    'name': 'Cow',
                }
            })

            response, = self.simulate_request('/animals/{}'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': {
                    'id': id,
                    'name': 'Cow',
                }
            })
            response, = self.simulate_request('/animals'.format(id), method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
            self.assertOK(response, {
                'data': [{
                    'id': id,
                    'name': 'Cow',
                }]
            })
