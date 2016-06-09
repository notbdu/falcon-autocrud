# Falcon-AutoCRUD

Makes RESTful CRUD easier.

## Test status

[ ![Codeship Status for garymonson/falcon-autocrud](https://codeship.com/projects/ed5bb4c0-b517-0133-757f-3e023a4cadff/status?branch=master)](https://codeship.com/projects/134046)

## IMPORTANT CHANGE IN 1.0.0

Previously, the CollectionResource and SingleResource classes took db_session
as a parameter to the constructor.  As of 1.0.0, they now take db_engine
instead.  The reason for this is to keep the sessions short-lived and under
autocrud's control to explicitly close the sessions.

This WILL impact you as your routing should now pass the db_engine instead of
the db_session, and if you override these classes, then, if you have overridden
the constructor, you may also have to update that.

## Quick start for contributing

```
virtualenv -p `which python3` virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt
pip install -r dev_requirements.txt
nosetests
```

This runs the tests with SQLite.  To run the tests with Postgres (using
pg8000), you must have a Postgres server running, and a postgres user with
permission to create databases:

```
export AUTOCRUD_DSN=postgresql+pg8000://myuser:mypassword@localhost:5432
nosetests
```

## Usage

Declare your SQLAlchemy models:

```
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id      = Column(Integer, primary_key=True)
    name    = Column(String(50))
    age     = Column(Integer)
```

Declare your resources:

```
from falcon_autocrud.resource import CollectionResource, SingleResource

class EmployeeCollectionResource(CollectionResource):
    model = Employee

class EmployeeResource(SingleResource):
    model = Employee
```

Apply them to your app, ensuring you pass an SQLAlchemy engine to the resource
classes:

```
from sqlalchemy import create_engine
import falcon
import falconjsonio.middleware

db_engine = create_engine('sqlite:///stuff.db')

app = falcon.API(
    middleware=[
        falconjsonio.middleware.RequireJSON(),
        falconjsonio.middleware.JSONTranslator(),
    ],
)

app.add_route('/employees', EmployeeCollectionResource(db_engine))
app.add_route('/employees/{id}', EmployeeResource(db_engine))
```

This automatically creates RESTful endpoints for your resources:

```
http GET http://localhost/employees
http GET http://localhost/employees?name=Bob
http GET http://localhost/employees?age__gt=24
http GET http://localhost/employees?age__gte=25
http GET http://localhost/employees?age__lt=25
http GET http://localhost/employees?age__lte=24
http GET http://localhost/employees?name__contains=John
http GET http://localhost/employees?name__startswith=John
http GET http://localhost/employees?company_id__null=1
http GET http://localhost/employees?company_id__null=0
echo '{"name": "Jim"}' | http POST http://localhost/employees
http GET http://localhost/employees/100
echo '{"name": "Jim"}' | http PUT http://localhost/employees/100
echo '{"name": "Jim"}' | http PATCH http://localhost/employees/100
http DELETE http://localhost/employees/100
# PATCHing a collection to add entities in bulk
echo '{"patches": [{"op": "add", "path": "/", "value": {"name": "Jim"}}]}' | http PATCH http://localhost/employees
```

### Identification and Authorization

Define classes that know how to identify and authorize users:

```
class TestIdentifier(object):
    def identify(self, req, resp, resource, params):
        req.context['user'] = req.get_header('Authorization')
        if req.context['user'] is None:
            raise HTTPUnauthorized('Authentication Required', 'No credentials supplied')

class TestAuthorizer(object):
    def authorize(self, req, resp, resource, params):
        if 'user' not in req.context or req.context['user'] != 'Jim':
            raise HTTPForbidden('Permission Denied', 'User does not have access to this resource')
```

Then declare which class identifies/authorizes what resource or method:

```
# Authorizes for all methods
@identify(TestIdentifier)
@authorize(TestAuthorizer)
class AccountCollectionResource(CollectionResource):
    model = Account

# Or only some methods
@identify(TestIdentifier)
@authorize(TestAuthorizer, methods=['GET', 'POST'])
@authorize(OtherAuthorizer, methods=['PATCH'])
class OtherAccountCollectionResource(CollectionResource):
    model = Account
```

### Filters/Preconditions

You may filter on GET, and set preconditions on single resource PATCH or DELETE:

```
class AccountCollectionResource(CollectionResource):
    model = Account

    def get_filter(self, req, resp, query, *args, **kwargs):
        # Only allow getting accounts below id 5
        return query.filter(Account.id < 5)

class AccountResource(SingleResource):
    model = Account

    def get_filter(self, req, resp, query, *args, **kwargs):
        # Only allow getting accounts below id 5
        return query.filter(Account.id < 5)

    def patch_precondition(self, req, resp, query, *args, **kwargs):
        # Only allow setting owner of non-owned account
        if 'owner' in req.context['doc'] and req.context['doc']['owner'] is not None:
            return query.filter(Account.owner == None)
        else:
            return query

    def delete_precondition(self, req, resp, query, *args, **kwargs):
        # Only allow deletes of non-owned accounts
        return query.filter(Account.owner == None)
```
