# Overview

This is a simple dashboarding application built using Flask and Bootstrap.  The application has been tested with Python 2.7.

Prerequisites
    Git - https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
    PostgreSQL - https://www.postgresql.org/download/
    Virtualenv - https://virtualenv.pypa.io/en/stable/installation/

# Installation

1. Creating Database named "tremap" using Postgres
    
  ```
  git clone https://github.com/livinggoods/mapping-tool.git
  ```

3. Create a virtualenv in the project directory
  
  ```
  cd mapping-tool
  virtualenv venv
  source venv/bin/activate
  ```

4. Installing dependencies

  ```
  pip install -r requirements.txt
  ```

5. Create Config File

  ```
  cp config.tmp.py config.py
  ```


6. Configure the application

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
  $  export RDS_DB_NAME=database
```


7. Building the database

  ```
  python manage.py db_rebuild
  ```

6. Start development server

  ```
  python manage.py runserver
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
  python manage.py db_rebuild
  ```

**Database Migrations**

1. Create an automatic migration upgrade script

  ```
  python manage.py db migrate -m "<migration message>"
  ```

2. Apply the migration upgrade script (note, upgrade script should be reviewed before applying changes)

  ```
  python manage.py  db upgrade
  ```

# Resources

* [Flask Documentation](http://flask.pocoo.org/)
* [Bootstrap Documentation](http://getbootstrap.com/)
* [SB Admin 2 Bootstrap Template](http://startbootstrap.com/template-overviews/sb-admin-2/)
* [Miguel Grinberg Flask Web Development Book](http://www.flaskbook.com/)