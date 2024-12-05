from flask import Flask, request, render_template, jsonify
from kubernetes import client, config

app = Flask(__name__)

# Load the Kubernetes configuration
config.load_kube_config()

# Create a Kubernetes API client
v1 = client.CoreV1Api()

def get_namespaces():
    # Get the list of namespaces
    namespaces = v1.list_namespace().items
    return [ns.metadata.name for ns in namespaces]

def get_pods_in_namespace(namespace):
    # List all pods in the specified namespace
    return v1.list_namespaced_pod(namespace=namespace).items

def get_pod_resources(pod):
    resources = {'cpu': {'request': '0', 'limit': '0'}, 'memory': {'request': '0', 'limit': '0'}}
    
    if pod.spec.containers:
        for container in pod.spec.containers:
            if container.resources:
                if container.resources.requests:
                    cpu_req = container.resources.requests.get('cpu', '0')
                    mem_req = container.resources.requests.get('memory', '0')
                    resources['cpu']['request'] = cpu_req
                    resources['memory']['request'] = mem_req
                
                if container.resources.limits:
                    cpu_limit = container.resources.limits.get('cpu', '0')
                    mem_limit = container.resources.limits.get('memory', '0')
                    resources['cpu']['limit'] = cpu_limit
                    resources['memory']['limit'] = mem_limit
    
    return resources

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get the list of namespaces
    namespaces = get_namespaces()
    
    if request.method == 'POST':
        # Get the selected namespace and list of pods in that namespace
        namespace = request.form.get('namespace')
        pods = get_pods_in_namespace(namespace)
        
        pod_list = []
        for pod in pods:
            # Get health status
            status = pod.status
            health = 'unknown'
            
            if status and status.container_statuses:
                all_ready = all(container.ready for container in status.container_statuses)
                all_running = all(container.state.running for container in status.container_statuses)
                
                if all_ready and all_running:
                    health = 'healthy'
                elif not all_ready or not all_running:
                    health = 'unhealthy'
            
            # Get container images
            images = []
            if pod.spec.containers:
                images = [container.image for container in pod.spec.containers]
            
            pod_list.append({
                'name': pod.metadata.name,
                'health': health,
                'image': images[0] if images else 'No image'
            })
        
        return jsonify(pod_list)
    
    return render_template('index.html', namespaces=namespaces)

@app.route('/namespaces')
def list_namespaces():
    # Get the list of namespaces
    namespaces = v1.list_namespace().items
    namespaces = [ns.metadata.name for ns in namespaces]
    
    # Return the list of namespaces as JSON
    return jsonify(namespaces)

@app.route('/api/images')
def api_list_images():
    # List all pods in all namespaces
    pods = v1.list_pod_for_all_namespaces(watch=False)

    # Extract the namespace, pod name, and Docker image for each pod
    images = []
    for pod in pods.items:
        container = pod.spec.containers[0]
        image = container.image
        image_filtered = image.split(':')[1] if ':' in image else image
        images.append({
            'namespace': pod.metadata.namespace,
            'pod_name': pod.metadata.name,
            'image': image_filtered
        })

    # Return the list of images as JSON
    return jsonify(images)

@app.route('/images')
def list_images():
    # Render the HTML page that will fetch data from the API
    return render_template('images.html')

@app.route('/api/images/<namespace>')
def api_get_namespace_images(namespace):
    # List all pods in the specified namespace
    pod_list = v1.list_namespaced_pod(namespace=namespace)

    # Extract the pod name and Docker image for each pod
    images = []
    for pod in pod_list.items:
        container = pod.spec.containers[0]
        image = container.image
        image_filtered = image.split(':')[1] if ':' in image else image
        images.append({
            'pod_name': pod.metadata.name,
            'image': image_filtered
        })

    # Return the list as JSON
    return jsonify(images)

@app.route('/images/<namespace>')
def get_image(namespace):
    # Render the HTML page that will fetch data from the API
    return render_template('pod.html', namespace=namespace)

@app.route('/dashboard')
def dashboard():
    namespaces = get_namespaces()
    return render_template('dashboard.html', namespaces=namespaces)

@app.route('/api/health/<namespace>')
def get_health_status(namespace):
    pods = get_pods_in_namespace(namespace)
    health_data = []
    
    for pod in pods:
        status = pod.status
        health = 'unknown'
        
        if status and status.container_statuses:
            all_ready = all(container.ready for container in status.container_statuses)
            all_running = all(container.state.running for container in status.container_statuses)
            
            if all_ready and all_running:
                health = 'healthy'
            elif not all_ready or not all_running:
                health = 'unhealthy'
        
        health_data.append({
            'name': pod.metadata.name,
            'health': health
        })
    
    return jsonify(health_data)

@app.route("/health/<namespace>")
def health(namespace):
    # Render the HTML page that will fetch data from the API
    return render_template("health.html", namespace=namespace)

@app.route('/api/pods/<namespace>')
def get_pod_data(namespace):
    pods = get_pods_in_namespace(namespace)
    pod_data = []
    
    for pod in pods:
        # Get health status
        status = pod.status
        health = 'unknown'
        
        if status and status.container_statuses:
            all_ready = all(container.ready for container in status.container_statuses)
            all_running = all(container.state.running for container in status.container_statuses)
            
            if all_ready and all_running:
                health = 'healthy'
            elif not all_ready or not all_running:
                health = 'unhealthy'
        
        # Get container images and resources
        images = []
        if pod.spec.containers:
            images = [container.image for container in pod.spec.containers]
        
        # Get resource usage
        resources = get_pod_resources(pod)
        
        # Get restart count
        restart_count = 0
        if status and status.container_statuses:
            restart_count = sum(container.restart_count for container in status.container_statuses)
        
        pod_data.append({
            'name': pod.metadata.name,
            'health': health,
            'image': images[0] if images else 'No image',
            'resources': resources,
            'age': pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else 'Unknown',
            'restarts': restart_count
        })
    
    return jsonify(pod_data)

@app.route('/pod/<namespace>/<pod_name>')
def pod_details(namespace, pod_name):
    return render_template('pod.html', namespace=namespace, pod_name=pod_name)

@app.route('/api/events/<namespace>')
def get_namespace_events(namespace):
    events = v1.list_namespaced_event(namespace=namespace)
    event_data = []
    
    for event in events.items:
        event_data.append({
            'type': event.type,
            'reason': event.reason,
            'message': event.message,
            'count': event.count,
            'first_timestamp': event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else None,
            'last_timestamp': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else None,
            'involved_object': event.involved_object.name
        })
    
    return jsonify(sorted(event_data, key=lambda x: x['last_timestamp'] if x['last_timestamp'] else '', reverse=True))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
