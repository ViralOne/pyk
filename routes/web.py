from flask import Blueprint, render_template, request, jsonify
from services.kubernetes import (
    get_namespaces, get_pods_in_namespace, get_pod_health,
    get_pod_images
)

web = Blueprint('web', __name__)

@web.route('/', methods=['GET', 'POST'])
def index():
    """Home page with namespace selection and pod list"""
    namespaces = get_namespaces()
    
    if request.method == 'POST':
        namespace = request.form.get('namespace')
        pods = get_pods_in_namespace(namespace)
        pod_list = []
        
        for pod in pods:
            health = get_pod_health(pod)
            images = get_pod_images(pod)
            
            pod_list.append({
                'name': pod.metadata.name,
                'health': health,
                'image': images[0] if images else 'No image'
            })
        
        return jsonify(pod_list)
    
    return render_template('index.html', namespaces=namespaces)

@web.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    namespaces = get_namespaces()
    return render_template('dashboard.html', namespaces=namespaces)

@web.route('/images')
def images():
    """Image overview page"""
    return render_template('images.html')

@web.route('/images/<namespace>')
def namespace_images(namespace):
    """Namespace-specific image page"""
    return render_template('pod.html', namespace=namespace)

@web.route('/pod/<namespace>/<pod_name>')
def pod_details(namespace, pod_name):
    """Detailed pod view"""
    return render_template('pod.html', namespace=namespace, pod_name=pod_name)

@web.route('/health/<namespace>')
def health(namespace):
    """Health status page"""
    return render_template('health.html', namespace=namespace)
