# Feature-limited NFT Marketplace - Challenge

## Quickstart

To deploy the application locally you must have `poetry` installed.<br>
To do so run the following command:

    curl -sSL https://install.python-poetry.org | python3 -

Then unzip de repo and install dependencies with `poetry`:

    unzip nft-marketplace.zip
    cd nft-marketplace
    poetry install
    poetry shell

Create `.env` file (or rename and modify `.env.example`) in project
root and set environment variables for application: :

    DB_HOST=mysql host localhost
    DB_PORT=mysql port 3306
    DB_USER=mysql user root
    DB_PASSWORD=mysql pwd root
    DB_NAME=mysql db mb_challenge

To run the web application locally first you must create the database:

    mysql -u root -e "create database mb_challenge"; 

Then start the app using the following poetry command:

    poetry run uvicorn nft_service.src.main:app --host 0.0.0.0 --port 5000


## Deployment with Docker

You must have `docker` and `docker-compose` tools installed to work with
material in this section. <br>First, create `.env` file like in <b>Quickstart</b>
section or modify `.env.example`. `DB_HOST` must be specified as `db` or modified in
`docker-compose.yml` also.
<br>Check `.env.docker` for default values.
Then just run:

    docker-compose up -d --build

Application will be available on `localhost:5000` in your browser.


## API documentation

All routes are available on `/docs` paths with Swagger
In the root directory there's a file containing the Postman Collection.

## Project structure

Files related to application are in the `nft_service` directory.
Application parts are:

    nft_service
    ├── db                  - db related stuff
    │   ├── repositories    - repository classes to be used by services
    |   |   ├── balance     - balance repository class
    |   |   ├── base        - base repository to be inherited by others
    |   |   ├── nft         - nft repository class
    |   |   ├── transaction - transaction repository class
    |   |   └── user        - user repository class
    │   ├── constants    - initializacion tables stuff
    │   └── events       - database creation and configuration
    ├── models          - db models related stuff
    │   ├── auditable   - base model to manage auditory related fields
    │   ├── balance     - balance related db models
    │   ├── exception   - exception models to be returned by endpoints
    │   ├── nft         - nft related db models
    │   ├── transaction - transaction related db models
    │   └── user        - user related db models
    ├── routers                 - web related stuff
    │   ├── routers             - setup endpoints and error handlers
    │   ├── nft_routers         - nft related endpoints
    │   ├── balance_routers     - balance related endpoints
    │   ├── transaction_routers - transaction related endpoints
    │   └── user_routers        - user related endpoints
    ├── schemas                - pydantic models to be used as request/response in endpoints
    │   ├── balance_schema     - balance related schemas
    │   ├── nft_schema         - nft related schemas
    │   ├── request_schema     - setup endpoints and error handlers
    │   ├── transaction_schema - schemas for general purposes, e.g. pagination
    │   └── user_schema        - user related schemas
    ├── services                - logic that is not just endpoint related
    │   ├── balance_service     - logic to manage user balance operations
    │   ├── base_service        - base class to be inherited by other services
    │   ├── nft_service         - logic to manage nft operations
    │   ├── transaction_service - logic to manage transactions when trading nfts
    │   └── user_service        - logic related to user operations
    ├── utils      - general purpose functions used in the application
    ├── config     - general configurations
    ├── context    - context definition to simulate login
    ├── exceptions - definitions for custom exceptions
    └── main.py    - FastAPI application creation and configuration
