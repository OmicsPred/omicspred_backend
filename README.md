# OmicsPred backend

Backend part of the OmicsPred Project

* OmicsPred website: [https://www.omicspred.org/](https://www.omicspred.org/)
* OmicsPred REST API website: [https://rest.omicspred.org/](https://rest.omicspred.org/)

## Roles
Manage import, querying and retrieval of the OmicsPred metadata:

* Scripts to import the metadata and generate the genetic scoring files (app [imports](https://github.com/OmicsPred/omicspred_backend/tree/main/imports))
* Access the databases (apps [omicspred](https://github.com/OmicsPred/omicspred_backend/tree/main/omicspred), [applications](https://github.com/OmicsPred/omicspred_backend/tree/main/applications), [plot](https://github.com/OmicsPred/omicspred_backend/tree/main/plot)) *[read & write]*
* Provide private (accessible by the website) and public REST APIs (app [rest_api](https://github.com/OmicsPred/omicspred_backend/tree/main/rest_api)) *[read only]*
* Build and query the search engine (app [search_es](https://github.com/OmicsPred/omicspred_backend/tree/main/search_es)) using ElasticSearch *[read & write]*

## Softwares / tools


| Tool | Role | Version |
| ---- | ---- | ------- |
| [PostgreSQL](https://www.postgresql.org/)| Database to store and query metadata | >= 15 |
| [ElasticSearch](https://www.elastic.co/) | Server used as search engine | 7.xx (e.g. 7.17) |
| [Django ](https://www.djangoproject.com/) | Python framework to communicate with the database, the ElasticSearch indexes and build a REST API | 5.2.x (e.g. 5.2.5) |


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

  * Main indexes

    ```bash
    python manage.py search_index --rebuild -f
    ```

  * Phenotype index

    * In *search_es/indexes.py*, comment all the lines and uncomment the PhenotypeDocument line
    * In *applications/models.py*, replace the line `applications_db = 'applications'` by `applications_db = 'default'`
    * In *config/settings.py*:
      * Comment the `DATABASE[‘default’]` items
      * Rename `DATABASE[‘applications’]` by `DATABASE[‘default’]`
    * Run script

      ```bash
      python manage.py search_index --rebuild -f
      ```

  > [!WARNING]
  > Do not forget to revert all these changes after generating the Phenotype search index!

* For **local** deployment, run the command:

  ```bash
  python manage.py runserver
  ```

  This will create an instance of the Django apps on your local machine on `http://127.0.0.1:8000/`

* For **cloud** deployment (e.g. Google Cloud App Engine), after setting up the Cloud account on your laptop and updating the **app.yaml** file, run the command:

  ```bash
  gcloud app deploy
  ```

> [!NOTE]
> You will need to deploy the backend twice:
>
> * One for the [Public REST API](https://rest.omicspred.org/) with the app deployment name `service: rest` and the variable `PUBLIC_SITE: 'True'`.
> * One for the **Private REST API** (i.e. the one consumed by the OmicsPred website) with the app deployment name `service: rest-private` and the variable `PUBLIC_SITE: 'False'`.  
> See the different **app.yaml** configuration files already set in the Group Google Drive directory `Website -> Systems/Settings -> REST API (back-end)`

## Tests

Tests have been written for the **metadata imports** and the **REST API**.
To run the tests manually, run the command:

```bash
python manage.py test
```

or to only run one test (e.g. metadata imports):

```bash
python manage.py test imports/tests
```
