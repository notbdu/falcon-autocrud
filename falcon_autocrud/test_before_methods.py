import falcon
import falcon.errors
import json
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .test_base import Base, BaseTestCase
from .test_fixtures import Account, Company

from .resource import CollectionResource, SingleResource


class Owner(Base):
    __tablename__ = 'owners'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    company_id  = Column(Integer, ForeignKey('companies.id'), nullable=False)
    company     = relationship('Company')

class AccountCollectionResource(CollectionResource):
    model = Account
    default_sort = ['id']

class BeforeAccountCollectionResource(CollectionResource):
    model = Account

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        if resource.name == 'Jack':
            raise falcon.errors.HTTPForbidden('Permission Denied', 'Jack is not allowed')
        extra_resource = Account(id=req.context['doc']['id'] + 10, name=req.context['doc']['name'] + ' 2')
        db_session.add(extra_resource)

class OwnerCollectionResource(CollectionResource):
    model = Owner

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        # Add related company
        company = Company(id=req.context['doc']['company_id'], name=req.context['doc']['company_name'])
        db_session.add(company)

class OwnerResource(SingleResource):
    model = Owner

    def before_patch(self, req, resp, db_session, resource, *args, **kwargs):
        # Rename company
        company = resource.company
        company.name = req.context['doc']['company_name']
        db_session.add(company)

class CompanyResource(SingleResource):
    model = Company

class MethodTest(BaseTestCase):
    def create_test_resources(self):
        self.app.add_route('/accounts', AccountCollectionResource(self.db_engine))
        self.app.add_route('/before-accounts', BeforeAccountCollectionResource(self.db_engine))
        self.app.add_route('/owners', OwnerCollectionResource(self.db_engine))
        self.app.add_route('/owners/{id}', OwnerResource(self.db_engine))
        self.app.add_route('/companies/{id}', CompanyResource(self.db_engine))

    def test_no_before(self):
        response, = self.simulate_request('/accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       1,
                'name':     'Bob',
                'owner':    None,
            }
        })

    def test_before(self):
        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 1, 'name': 'Bob'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       1,
                'name':     'Bob',
                'owner':    None,
            }
        })

        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 2, 'name': 'Jim'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':       2,
                'name':     'Jim',
                'owner':    None,
            }
        })

        response, = self.simulate_request('/before-accounts', method='POST', body=json.dumps({'id': 3, 'name': 'Jack'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertForbidden(response, 'Jack is not allowed')

        response, = self.simulate_request('/accounts', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': [
                {'id': 1, 'name': 'Bob', 'owner': None},
                {'id': 2, 'name': 'Jim', 'owner': None},
                {'id': 11, 'name': 'Bob 2', 'owner': None},
                {'id': 12, 'name': 'Jim 2', 'owner': None},
            ]
        })

    def test_add_or_update_related_data(self):
        response, = self.simulate_request('/owners', method='POST', body=json.dumps({'id': 1, 'name': 'Bob', 'company_id': 5, 'company_name': 'Initech'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertCreated(response, {
            'data': {
                'id':           1,
                'name':         'Bob',
                'company_id':   5,
            }
        })
        response, = self.simulate_request('/companies/5', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':           5,
                'name':         'Initech',
            }
        })

        response, = self.simulate_request('/owners/1', method='PATCH', body=json.dumps({'name': 'Jack', 'company_name': 'Vandelay'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':           1,
                'name':         'Jack',
                'company_id':   5,
            }
        })
        response, = self.simulate_request('/companies/5', method='GET', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertOK(response, {
            'data': {
                'id':           5,
                'name':         'Vandelay',
            }
        })
