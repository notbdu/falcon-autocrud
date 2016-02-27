# Falcon-AutoCRUD

Makes RESTful CRUD easier.

## Test status

[ ![Codeship Status for garymonson/falcon-autocrud](https://codeship.com/projects/ed5bb4c0-b517-0133-757f-3e023a4cadff/status?branch=master)](https://codeship.com/projects/134046)

## Quick start for contributing

    virtualenv -p `which python3` virtualenv
    source virtualenv/bin/activate
    pip install -r requirements.txt
    pip install -r dev_requirements.txt
    nosetests

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

Apply them to your app, ensuring you pass an SQLAlchemy session to the resource
classes:

```
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine
import falcon
import falconjsonio.middleware

Session     = sessionmaker()
db_engine   = create_engine('sqlite:///stuff.db')
db_session  = Session(bind=db_engine)

app = falcon.API(
    middleware=[
        falconjsonio.middleware.RequireJSON(),
        falconjsonio.middleware.JSONTranslator(),
    ],
)

app.add_route('/employees', EmployeeCollectionResource(db_session))
app.add_route('/employees/{id}', EmployeeResource(db_session))
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
echo '{"name": "Jim"}' | http POST http://localhost/employees
http GET http://localhost/employees/100
echo '{"name": "Jim"}' | http PUT http://localhost/employees/100
echo '{"name": "Jim"}' | http PATCH http://localhost/employees/100
http DELETE http://localhost/employees/100
# PATCHing a collection to add entities in bulk
echo '{"patches": [{"op": "add", "path": "/", "value": {"name": "Jim"}}]}' | http PATCH http://localhost/employees
```
