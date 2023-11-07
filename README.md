# Chatrooms server

Chatrooms server is the server for a instant messaging app.

## Installation

This project use [PDM](https://pdm-project.org/latest/) as a package manager and builder

```sh
pdm install
```

## Usage

You should have access to a running PostgreSQL database;
by default the application will try to connect to: `postgresql://postgres:postgres@localhost:5432`

Run server in development mode

```sh
pdm run start
```

Run tests

```sh
pdm run tests
```
