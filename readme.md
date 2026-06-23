<p align="center">
  <img src="framework/nest/assets/images/mouse_logo_circle.png" alt="Mouse Logo" width="256" height="256">
</p>

# Mouse

A Python MVC Web Framework inspired by Laravel

## Tested Environnment

- Docker
    - Windows 10
    - Linux Mint 22
    - Zorin OS 18
    - Ubuntu 24.04 LTS
- On host
    - Windows 10
    - Linux Mint 22
    - Zorin OS 18
    - Ubuntu 24.04 LTS

## Installation

```bash
pip install mouse-cli
mouse-cli new project MyProject
```
- Copy ".env.example"
- Paste
- Rename the copy for ".env"
- python server.py
- If port 8080 is already in use:
    ```bash
    sudo fuser -k 8080/tcp
    ```

## Cloning Procedure

- ```bash
    git clone https://github.com/Dolotboy/Mouse
    ```
- ```bash
    cd mouse
    ```
- Copy ".env.example"
- Paste
- Rename the copy for ".env"


## Dependencies

- [Python 3.12](https://www.python.org/downloads/)
- [Python DotEnv](https://pypi.org/project/python-dotenv/)
    - ```bash 
        pip install python-dotenv
        ```
- [MySQL Connector/Python](https://pypi.org/project/mysql-connector-python/) for MySQL connections

## Framework structure
[Documentation](/framework/readme.md)

## Database and migrations

Configure the database in `.env` with `DB_CONNECTION=mysql` or `DB_CONNECTION=sqlite`.
```bash
mouse-cli new db
mouse-cli new migration create_users_table
mouse-cli migrate
mouse-cli migrate:rollback
```

Migration files are created in `web/database/migrations`.

## Views

## Models

## Controllers
