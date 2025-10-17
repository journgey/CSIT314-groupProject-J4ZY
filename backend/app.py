from flask import Flask
from flask_cors import CORS
from repository.db import init_db
from controllers.requests_controller import requests_bp
from controllers.accounts_controller import accounts_bp   # NEW
from controllers.categories_controller import categories_bp  # NEW

def create_app():
    app = Flask(__name__)
    CORS(app)  # ★ 프론트엔드 파일에서 API 호출 허용
    init_db()
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")      # NEW (목록용)
    app.register_blueprint(categories_bp, url_prefix="/api/categories")  # NEW (목록용)
    app.register_blueprint(requests_bp, url_prefix="/api/requests")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
