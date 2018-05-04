# Overview

This is a simple dashboarding application built using Flask and Bootstrap.  The application has been tested with Python 2.7.



# Installation

1. Clone the repository

  ```
  git clone https://github.com/livinggoods/mapping-tool.git
  ```

2. Create a virtualenv in the project directory

  ```
  cd mapping-tool
  virtualenv venv
  source venv/bin/activate
  ```

3. Install dependencies

  ```
  pip install -r requirements.txt
  ```

4. Create database

  ```
  ./manage db_rebuild
  ```

5. Configure the application

For your application to run properly, you need to set the following environment variables.
RDS_USERNAME: The authorized username to the Postgres instance
RDS_PASSWORD: The password for the username (above)
RDS_HOSTNAME: The server name or IP of the Postgres server
RDS_PORT: The Postgres port
RDS_DB_NAME: The database name

To setup the above variables, you can run the following commands. Be sure to change them to suit your server
```
  $  export RDS_USERNAME=username
  $  export RDS_PASSWORD=password
  $  export RDS_HOSTNAME=localhost
  $  export RDS_PORT=5432
  $   export RDS_DB_NAME=database
```

5. Run tests

  ```
  ./manage.py test
  ```

6. Start development server

  ```
  ./manage.py runserver
  ```

# Database Operations

**PostgreSQL Database Operations**

1. `pg_ctl` is a utility to initialize, start, stop, or control a PostgreSQL server.
  * `pg_ctl status -D DATADIR` shows the status of a PostgreSQL database.
  * `pg_ctl start -D DATADIR` starts the PostgreSQL server
  * `pg_ctl stop -D DATADIR` stops the PostgreSQL server.
  * `pg_ctl stop -D DATADIR -m fast` immediately stops the PostgreSQL server rather than waiting for session-initiated disconnection.
2. `postgres` is the PostgreSQL server.
  * `postgres -D DATADIR` starts the PostgreSQL server.
3. `psql` is the PostgreSQL interactive terminal.
  * `psql -d DATABASE` connects to a given database.
  * `psql -l` lists all available databases.

**Destroy and Rebuild Database**

1. The positional argument 'db_rebuild' will delete any existing sqlite database and create a new devlopment database populated with fake data.

  ```
  ./manage db_rebuild
  ```

**Database Migrations**

1. Create an automatic migration upgrade script

  ```
  ./manage db migrate -m "<migration message>"
  ```

2. Apply the migration upgrade script (note, upgrade script should be reviewed before applying changes)

  ```
  ./manage db upgrade
  ```

# Resources

* [Flask Documentation](http://flask.pocoo.org/)
* [Bootstrap Documentation](http://getbootstrap.com/)
* [SB Admin 2 Bootstrap Template](http://startbootstrap.com/template-overviews/sb-admin-2/)
* [Miguel Grinberg Flask Web Development Book](http://www.flaskbook.com/)
* [Miguel Grinberg Flask Web Development GitHub](https://github.com/miguelgrinberg/flasky)

# Flask Extensions
* [Flask Bootstrap](http://pythonhosted.org/Flask-Bootstrap/)
* [Flask Mail](https://pythonhosted.org/Flask-Mail/)
* [Flask Moment](https://github.com/miguelgrinberg/flask-moment/)
* [Flask SQLAlchemy](https://pythonhosted.org/Flask-SQLAlchemy/)
* [Flask Migrate](https://flask-migrate.readthedocs.org/en/latest/)
* [Flask Login](https://flask-login.readthedocs.org/en/latest/)
* [Flask Script](http://flask-script.readthedocs.org/en/latest/)


# Points to note
## Installation Errors
When installing the dependencies, you might experience an error with psycopg2.

```

Command "/usr/bin/python -u -c "import setuptools, tokenize;__file__='/tmp/pip-build-WSjqit/psycopg2/setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\r\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" install --record /tmp/pip-db6s9R-record/install-record.txt --single-version-externally-managed --compile" failed with error code 1 in /tmp/pip-build-WSjqit/psycopg2/

```
To solve this problem you need run the following command (tested on Ubuntu)
`sudo apt-get install python-dev postgresql-libs postgresql-devel`



Maintained by [David Kimaru](https://github.com/kimarudg)
