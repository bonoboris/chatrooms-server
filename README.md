# Chatrooms server

Chatrooms server is the server for chatrooms, an instant messaging app (see [client](https://github.com/bonoboris/chatrooms-client)).

Chatrooms is a showcase project of a full-stack web application.

## Installation

This project use [PDM](https://pdm-project.org/latest/) as a package manager and builder

```sh
pdm install
```

## Usage

You should have access to a running PostgreSQL database;
by default the application will try to connect with user `postgres:postgres` using a UNIX socket (`/var/run/postgresql`).

Run server in development mode

```sh
pdm dev
```

Run tests

```sh
pdm test
```
