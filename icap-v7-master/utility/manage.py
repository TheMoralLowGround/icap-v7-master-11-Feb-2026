from flask.cli import FlaskGroup

from flask_app import app


cli = FlaskGroup(app)


if __name__ == "__main__":
    cli()