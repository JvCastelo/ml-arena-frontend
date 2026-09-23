from flask import Flask, redirect, url_for


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-not-for-production"

    from .routes.runs import runs_bp
    from .routes.compare import compare_bp

    app.register_blueprint(runs_bp)
    app.register_blueprint(compare_bp)

    @app.get("/")
    def index():
        return redirect(url_for("runs.list_runs"))

    return app
