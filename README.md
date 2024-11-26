# Chatrooms server

Chatrooms server is the server for chatrooms, an instant messaging app (see [client](https://github.com/bonoboris/chatrooms-client)).

Chatrooms is a showcase project of a full-stack web application.

## Installation

This project use [PDM](https://pdm-project.org/latest/) as a package manager and builder

```sh
pdm install
```

The application requires:

- a PostgreSQL database (by default `chatrooms`).

  It can be created with the following command (as the default admin user `postgres`):

  ```sh
  sudo --user postgres createdb chatrooms
  ```

- a folder to store uploaded files (by default `/data/chatrooms`).

  It must be writable by the user running the application (not necessarly the DB user).

  ```sh
  sudo mkdir --parents /data/chatrooms
  sudo chown --recursive <user> /data/chatrooms
  ```

After creating the database, you will need to run the `migrate` CLI to create the tables:

```sh
migrate up --all
```

### OS User / PG User

For development, to connect to the database you can:

- create a postgres user with the same name as your OS user name and set the `CHATROOMS_SERVER_PG_USER` environment variable to this user.

  ```sh
  sudo --user postgres createuser --superuser <user>
  ```

- map your OS user name to the `postgres` user

  - locate the `pg_ident.conf` file (`/etc/postgresql/16/main/pg_ident.conf` for PostgreSQL 16 on Ubuntu)
  - add the following line at the end: `mymap <user> postgres`
  - locate the `pg_hba.conf` file (`/etc/postgresql/16/main/pg_hba.conf` for PostgreSQL 16 on Ubuntu)
  - locate and modify the line
    ```text
    local  all  postgres  peer
    ```
    to
    ```text
    local  all  postgres  peer  map=mymap
    ```
  - restart the PostgreSQL server
    ```sh
    sudo systemctl restart postgresql
    ```

## Configuration

The application can be configured using environment variables.

| Name                                     | Default Value     | Description                                            |
| ---------------------------------------- | ----------------- | ------------------------------------------------------ |
| `CHATROOMS_SERVER_PG_USER`               | `postgres`        | PostgreSQL database user                               |
| `CHATROOMS_SERVER_PG_PASSWORD`           | `postgres`        | PostgreSQL database user password                      |
| `CHATROOMS_SERVER_PG_HOST`               | ` `               | PostgreSQL database host (empty for unix socket)       |
| `CHATROOMS_SERVER_PG_PORT`               | `5432`            | PostgreSQL database port                               |
| `CHATROOMS_SERVER_PG_DATABASE`           | `chatrooms`       | PostgreSQL database name                               |
| `CHATROOMS_SERVER_FS_ROOT`               | `/data/chatrooms` | File systeme root folder for uploaded files            |
| `CHATROOMS_SERVER_SECRET_KEY`            | `secret`          | Secret key used to sign JWT tokens                     |
| `CHATROOMS_SERVER_ACCESS_TOKEN_EXPIRES`  | `1800` (30 mins)  | Access token expiration time in seconds                |
| `CHATROOMS_SERVER_REFRESH_TOKEN_EXPIRES` | `86400` (1 day)   | Access token expiration time in seconds                |
| `CHATROOMS_SERVER_COOKIE_MAX_AGE`        | `7200` (2 hours)  | Cookie max age in seconds for the authorization cookie |

## Usage

Run server in development mode

```sh
uvicorn 'chatrooms.main:app' --reload --reload-dir src
# or
pdm dev
```

Run tests

```sh
pytest
# or
pdm test
```
