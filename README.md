# OmicsPred backend

Backend part of the OmicsPred Project

* OmicsPred website: [https://www.omicspred.org/](https://www.omicspred.org/)
* OmicsPred REST API website: [https://rest.omicspred.org/](https://rest.omicspred.org/)

## Roles
Manage import, querying and retrieval of the OmicsPred metadata:

* Scripts to import the metadata and generate the genetic scoring files (app [imports](https://github.com/OmicsPred/omicspred_backend/tree/main/imports) -> [README](https://github.com/OmicsPred/omicspred_backend/tree/main/imports/README.md))
* Scripts to export the metadata and data (app [exports](https://github.com/OmicsPred/omicspred_backend/tree/main/exports))
* Access the databases (apps [omicspred](https://github.com/OmicsPred/omicspred_backend/tree/main/omicspred), [plot](https://github.com/OmicsPred/omicspred_backend/tree/main/plot)) *[read & write]*
* Provide private (accessible by the website) and public REST APIs (app [rest_api](https://github.com/OmicsPred/omicspred_backend/tree/main/rest_api)) *[read only]*
* Build and query the search engine (app [search_es](https://github.com/OmicsPred/omicspred_backend/tree/main/search_es)) using ElasticSearch *[read & write]*

## Softwares / tools

| Tool | Role | Version |
| ---- | ---- | ------- |
| [PostgreSQL](https://www.postgresql.org/)| Database to store and query metadata | >= 18 |
| [ElasticSearch](https://www.elastic.co/) | Server used as search engine | 8.xx (e.g. 8.19) |
| [Django ](https://www.djangoproject.com/) | Python framework to communicate with the database, the ElasticSearch indexes and build a REST API | 6.0.x (e.g. 6.0.7) |


## Setup

Go to root of the repository (e.g. `cd .../omicspred_backend`)

* Rename [app.yaml_template](https://github.com/OmicsPred/omicspred_backend/blob/main/app.yaml_template) to **app.yaml** and replace the *&lt;values&gt;* with your settings
* Install the required Python packages with the commands:

  ```bash
  pip install -r requirements.txt
  pip install -r requirements_local.txt # Only necessary for local deployement
  ```

* Create **static** directory

  ```bash
  python manage.py collectstatic
  ```

* Create **ElasticSearch** indexes

  ```bash
  python manage.py search_index --create
  ```

  > [!WARNING]
  > The indexing of the scores takes few hours (2-3h)!

  To rebuild existing OmicsPred indexes:

  ```bash
    python manage.py search_index --rebuild -f
  ```

## Deployment

First of all, you need to rename and then update the file `app.yaml_template` to `app.yaml`.

### Local

Run the command:
```bash
python manage.py runserver
```

This will create an instance of the Django apps on your local machine on `http://127.0.0.1:8000/`

### Cloud

For **cloud** deployment (e.g. Google Cloud App Engine), after setting up the Cloud account on your laptop and updating the **app.yaml** file, run the command:

  ```bash
  gcloud app deploy
  ```

> [!NOTE]
> You will need to deploy the backend twice:
>
> * One for the [Public REST API](https://rest.omicspred.org/) with the app deployment name `service: rest` and the variable `PUBLIC_SITE: 'True'`.
> * One for the **Private REST API** (i.e. the one consumed by the OmicsPred frontend website) with the app deployment name, e.g. `service: rest-private`, and the variable `PUBLIC_SITE: 'False'`.
> See the different **app.yaml** configuration files already set in the Group Google Drive directory `Website -> Systems/Settings -> REST API (back-end)`.

## Tests

Tests have been written for the **metadata imports** and the **REST API**.
To run the tests manually, run the command:

```bash
python manage.py test
```

> [!NOTE]
> This runs the REST API, exports and imports tests

or to only run one test (e.g. metadata imports):

```bash
python manage.py test imports/tests
```
