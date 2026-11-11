import os
import click
from flask import Flask, jsonify
from flask.cli import with_appcontext
from flask_login import UserMixin, LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import URL
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "index"
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        APP_ENV=os.environ.get("APP_ENV", "beta"),
        SESSION_COOKIE_NAME=os.environ.get("SESSION_COOKIE_NAME", "session"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
    )
    if test_config is not None:
        app.config.update(SECRET_KEY="test-secret")
        app.config.update(test_config)
    else:
        db_type = os.environ["DB_TYPE"]
        if db_type == "sqlite":
            uri = "sqlite:///" + os.environ["DB_NAME"]
        elif db_type in {"mariadb", "postgresql"}:
            uri = URL.create(
                "mysql+pymysql" if db_type == "mariadb" else "postgresql",
                username=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]),
                database=os.environ["DB_NAME"],
            )
        else:
            raise RuntimeError("Tipo di database non supportato")
        app.config.update(SQLALCHEMY_DATABASE_URI=uri, SECRET_KEY=os.environ["SECRET_KEY"])
        if not app.config["SECRET_KEY"]:
            raise RuntimeError("SECRET_KEY non può essere vuota")
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    app.cli.add_command(init_db)

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify(status="error", response="csrf_invalid"), 400

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify(status="error", response="forbidden"), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(status="error", response="not_found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify(status="error", response="internal_error"), 500

    @app.context_processor
    def environment_label():
        return {"is_development": app.config["APP_ENV"] == "development"}

    @app.get("/health")
    def health():
        try:
            User.query.limit(1).all()
        except Exception:
            db.session.rollback()
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok")

    from routes import init_routes
    init_routes(app)
    return app


@click.command("init-db")
@with_appcontext
def init_db():
    if User.query.first() is not None:
        raise click.ClickException("Database già inizializzato: nessuna modifica.")
    initial_password = os.environ.get("INITIAL_ADMIN_PASSWORD")
    if not initial_password:
        initial_password = click.prompt("Password amministratore", hide_input=True, confirmation_prompt=True)
    if len(initial_password) < 12:
        raise click.ClickException("Usare una password di almeno 12 caratteri.")
    password = generate_password_hash(initial_password)
    db.session.add(GruppiUser(name="admin", permessi=["MY_EVENTS","ALL_EVENTS","DASHBOARD","EVENTS","SETTINGS","ACCOUNT"]))
    db.session.flush()
    gruppo = GruppiUser.query.filter_by(name="admin").first()
    db.session.add(User(username="admin", password=password, nome="Nome", cognome="Cognome", mail="mail@esempio.it", gruppo=gruppo.id))

    db.session.add(SysOption(key="id_ente", value="Nome Ente"))
    db.session.add(SysOption(key="nome_iro", value="Nome"))
    db.session.add(SysOption(key="cognome_iro", value="Cognome"))
    db.session.add(SysOption(key="smtp_server", value="smtp.gmail.com"))
    db.session.add(SysOption(key="smtp_port", value=587))
    db.session.add(SysOption(key="mail_indirizzo", value="mail@esempio.it"))
    db.session.add(SysOption(key="mail_passwd", value="PASSWORD"))

    db.session.add(TipoTransazione(nome="E1", tipo="E", descrizione="E1 - anticipo da segreteria", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="E2", tipo="E", descrizione="E2 - quota saldo iscritti (al campo)", calcolata=True, formula="[[quota_saldo]]*[[partecipanti]]"))
    db.session.add(TipoTransazione(nome="E3", tipo="E", descrizione="E3 - quota campo staff", calcolata=True, formula="[[staff]]*[[quota_staff]]"))
    db.session.add(TipoTransazione(nome="E4", tipo="E", descrizione="E4 - altre entrate", calcolata=False, formula=""))

    db.session.add(TipoTransazione(nome="U1", tipo="U", descrizione="U1 - pernottamento", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U2", tipo="U", descrizione="U2 - viveri", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U3", tipo="U", descrizione="U3 - spostamenti", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U4", tipo="U", descrizione="U4 - materiale", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U5", tipo="U", descrizione="U5 - rimborsi staff", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U6", tipo="U", descrizione="U6 - spese sostenute da segreteria", calcolata=False, formula=""))
    db.session.add(TipoTransazione(nome="U7", tipo="U", descrizione="U7 - spese sostenute da segreteria detratte dall'anticipo'", calcolata=False, formula=""))

    db.session.add(TipoVariabile(nome="num_quote_segreteria", formula="[[iscritti]]"))
    db.session.add(TipoVariabile(nome="quota_staff", formula="([[quota_acconto]]+[[quota_saldo]])/2"))
    db.session.add(TipoVariabile(nome="U6_U7", formula="[[U6]]+[[U7]]"))

    db.session.commit()
    print("Database inizializzato")

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


from models import User, GruppiUser, SysOption, TipoTransazione, TipoVariabile

app = create_app()

if __name__ == "__main__":
    app.run(port=8000, host="0.0.0.0")
