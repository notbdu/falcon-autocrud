# Falcon-AutoCRUD

Makes RESTful CRUD easier.

## Quick start for contributing

    virtualenv -p `which python3.4` virtualenv
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
echo '{"name": "Jim"}' | http POST http://localhost/employees
http GET http://localhost/employees/100
echo '{"name": "Jim"}' | http PUT http://localhost/employees/100
echo '{"name": "Jim"}' | http PATCH http://localhost/employees/100
http DELETE http://localhost/employees/100
```
