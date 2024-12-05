from flask import Flask, render_template, jsonify, request
from routes.web import web
from routes.api import api
from utils.config import Config
from services.kubernetes import get_pods_in_namespace, get_namespaces, get_pod_health
from services.statistics import get_cluster_stats

app = Flask(__name__)
app.register_blueprint(web)
app.register_blueprint(api, url_prefix='/api')

@app.context_processor
def inject_stats():
    """Inject cluster statistics into all templates"""
    stats = get_cluster_stats()
    return stats

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )