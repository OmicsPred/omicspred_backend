# OmicsPred backend

* OmicsPred website: [https://www.omicspred.org/](https://www.omicspred.org/)
* OmicsPred REST API website: [https://rest.omicspred.org/](https://rest.omicspred.org/)

## Roles
* Scripts to import the metadata and generate the genetic scoring files (app [imports](https://github.com/OmicsPred/omicspred_backend/tree/main/imports))
* Access the databases (apps [omicspred](https://github.com/OmicsPred/omicspred_backend/tree/main/omicspred), [applications](https://github.com/OmicsPred/omicspred_backend/tree/main/applications), [plot](https://github.com/OmicsPred/omicspred_backend/tree/main/plot)) *[read & write]*
* Provide private (accessible by the website) and public REST APIs (app [rest_api](https://github.com/OmicsPred/omicspred_backend/tree/main/rest_api)) *[read only]*
* Build and query the search engine (app [search_es](https://github.com/OmicsPred/omicspred_backend/tree/main/search_es)) using ElasticSearch *[read & write]*

## Setup

Go to root of the repository (e.g. `cd .../omicspred_backend`)

* Rename [app.yaml_template](https://github.com/OmicsPred/omicspred_backend/blob/main/app.yaml_template) to **app.yaml** and replace the *&lt;values&gt;* with your settings
* Install the required Python packages with the commands:
    ```
    pip install -r requirements.txt
    pip install -r requirements_local.txt # Only necessary for local deployement
    ```

* For **local** deployment, run the command:
    ```
    python manage.py runserver
    ```
    This will create an instance of the Django apps on your local machine on `http://127.0.0.1:8000/`

* For **cloud** deployment (e.g. Google Cloud App Engine), after setting up the Cloud account on your laptop, run the command:
    ```
    gcloud app deploy
    ```

## Tests

Tests have been written for the **metadata imports** and the **REST API**.
To run the tests manually, run the command:

    python manage.py test

or to only run one test (e.g. metadata imports):

    python manage.py test imports/tests

