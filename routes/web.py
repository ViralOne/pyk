from flask import Blueprint, render_template, redirect, url_for
from services.kubernetes import (
    get_namespaces
)

web = Blueprint('web', __name__)

@web.route('/', methods=['GET'])
def index():
    """Main dashboard/overview page"""
    namespaces = get_namespaces()
    return render_template('dashboard.html', namespaces=namespaces)

@web.route('/images')
def images():
    """Image overview page"""
    return render_template('images.html')

@web.route('/namespace/<namespace>')
def namespace_view(namespace):
    """Combined namespace view with health, images, and events"""
    return render_template('namespace.html', namespace=namespace)

# Redirect old routes to new namespace view
@web.route('/images/<namespace>')
def namespace_images(namespace):
    """Redirect to namespace view"""
    return redirect(url_for('web.namespace_view', namespace=namespace))

@web.route('/health/<namespace>')
def health(namespace):
    """Redirect to namespace view"""
    return redirect(url_for('web.namespace_view', namespace=namespace))
