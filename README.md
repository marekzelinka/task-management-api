# Task management REST API

Task management REST API built with **FastAPI** and **SQLAlchemy**. This project manages a database of tasks, project, with user auth using oauth, using a robust **Python** stack designed for speed and developer ergonomics.

## 🚀 Features

- **High-Performance API**: Fully asynchronous endpoints leveraging `FastAPI` and `SQLAlchemy`.
- **CRUD Operations**: Complete management for **Tasks**, **Projects**.
- **Relational Data**: Complex relationships handled seamlessly via SQLAlchemy.
- **Auto-Generated Documentation**: Interactive API docs available via **OpenAPI (Swagger UI)**.
- **Modern Tooling**: Managed with `uv` for lightning-fast environment and dependency resolution.
- **Code Quality**: Strict linting and formatting using `Ruff` and type checking using `ty`.
- **Database Migrations**: Version-controlled schema changes with `Alembic`.

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM/Models**: [SQLAlchemy](https://www.sqlalchemy.org/) (Async SQLAlchemy + Pydantic)
- **Database**: [SQLite](https://sqlite.org/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter/Formatter**: [Ruff](https://docs.astral.sh/ruff/)
- **Type Checker**: [ty](https://docs.astral.sh/ty/)

- Command Runner (optional extension): [just](https://just.systems/)

## 🏗 Setup

### Prerequisites

This project uses the modern `pyproject.toml` standard for dependency management and requires the `uv` tool to manage the environment.

**Ensure `uv` is installed** globally on your system. If not, follow the official installation guide for [`uv`](https://docs.astral.sh/uv/).

Create a [Neon account](https://console.neon.tech/signup) for serverless Postgres.

### Installation

1.  **Create environment and install dependencies:**

    ```sh
    uv sync
    ```

2.  **Set up Environment Variables:**

    Copy the contents of [`.env.example`](./.env.example) to `.env` file in the root directory.
    
     ```sh
    cp .env.example .env
    ```

3.  **Run Migrations:**

    Initialize your SQLite database to the latest schema:

    ```sh
    uv run alembic upgrade head
    ```

### Running the Application

Start the development server using `uv`:

```sh
uv run uvicorn app.main:app --reload
```

Once started, access the interactive docs at: [http://localhost:8000/docs](http://localhost:8000/docs).

### 💻 Local Development

1. Setup your editor to work with [ruff](https://docs.astral.sh/ruff/editors/setup/) and [ty](https://docs.astral.sh/ty/editors/).

2. Install the [justfile extension](https://just.systems/man/en/editor-support.html) for your editor, and use the provided `./justfile` to run commands.

## Code Quality

- Check for linting errors using `ruff check`: 

  ```sh
  uv run ruff check --fix
  ```

- Format the code using `ruff format`: 

  ```sh
  uv run ruff format
  ```

- Run typechecker using `pyrefly check`: 

  ```sh
  uv run pyrefly check
  ```

## TODO

- [x] user auth
- [x] projects route 
- [x] projects have many tasks
- [x] task belong to one project
- [x] add `due_date` to tasks
- [ ] bulk actions for tasks, DELETE and PATCH
- [x] explore async SQLAlchemy
- [x] Tags/Labels, table: Tag, fields:id, name, color_hex, user_id, relationship: Many-to-Many with task.
- [ ] add color hex field to project
