# URBANDICIONARY_BE

### Local setup

* Set up virtual environment

```bash
$ pip install uv
$ uv venv
```
* Install requirements

```bash
$ source .venv/bin/activate
$ uv pip install requirements.txt
```

* Set up DB

```bash
$ systemctl start docker
$ docker pull postgres  #only when first time
$ docker run --name some-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres
$ cd project
$ python3 manage.py migrate

* Test

```bash
$ source .venv/Scripts/activate
$ cd project
$ py.test
```
* Run server dev

```bash
$ cd project
$ python3 manage.py runserver
```

* Run server prod

```bash
$ docker compose up --build
