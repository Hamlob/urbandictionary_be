# URBANDICIONARY_BE

### Local setup

* Set up virtual environment

```bash
$ python3 -m venv venv
```
* Install requirements

```bash
$ source venv/bin/activate
$ python3 -m pip install requirements.txt
```

* Set up DB

```bash
$ docker pull postgres
$ docker run --name some-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres
$ cd project
$ python3 manage.py migrate

* Test

```bash
$ source venv/Scripts/activate
$ cd project
$ py.test
```
* Run server

```bash
$ cd project
$ python3 manage.py runserver
```
