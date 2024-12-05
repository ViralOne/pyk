from flask import Blueprint, jsonify
from functools import wraps
from services.kubernetes import (
    get_pods_in_namespace, get_pod_health, get_pod_resources,
    get_pod_images, get_pod_restart_count, get_namespace_events,
    get_all_pods, get_namespaces
)

api = Blueprint('api', __name__)

def handle_kubernetes_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return decorated_function

@api.route('/pods/<namespace>')
@handle_kubernetes_errors
def get_pod_data(namespace):
    """Get detailed pod information for a namespace"""
    pods = get_pods_in_namespace(namespace)
    pod_data = []
    
    for pod in pods:
        # Get health status and images
        health = get_pod_health(pod)
        images = get_pod_images(pod)
        
        # Get resource usage and restart count
        resources = get_pod_resources(pod)
        restart_count = get_pod_restart_count(pod)
        
        pod_data.append({
            'name': pod.metadata.name,
            'health': health,
            'image': images[0] if images else 'No image',
            'resources': resources,
            'age': calculate_age(pod.metadata.creation_timestamp),
            'restarts': restart_count
        })
    
    return jsonify(pod_data)

@api.route('/health/<namespace>')
@handle_kubernetes_errors
def get_health(namespace):
    """Get health status for pods in a namespace"""
    pods = get_pods_in_namespace(namespace)
    health_data = []
    
    for pod in pods:
        # Get all pod details
        health = get_pod_health(pod)
        resources = get_pod_resources(pod)
        restart_count = get_pod_restart_count(pod)
        
        # Calculate age
        age = calculate_age(pod.metadata.creation_timestamp)
        
        # Get status
        status = 'Unknown'
        if pod.status and pod.status.phase:
            status = pod.status.phase
        
        # Format CPU and memory
        cpu = resources['cpu']['request']
        memory = resources['memory']['request']
        
        if cpu == '0':
            cpu = 'N/A'
        if memory == '0':
            memory = 'N/A'
        
        health_data.append({
            'name': pod.metadata.name,
            'status': status,
            'health': health,
            'cpu': cpu,
            'memory': memory,
            'restarts': restart_count,
            'age': age
        })
    
    return jsonify(health_data)

@api.route('/events/<namespace>')
@handle_kubernetes_errors
def get_events(namespace):
    """Get events for a namespace"""
    events = get_namespace_events(namespace)
    formatted_events = []
    
    for event in events:
        # Calculate time since last event
        if event['last_timestamp']:
            from datetime import datetime
            last_time = datetime.strptime(event['last_timestamp'], "%Y-%m-%d %H:%M:%S")
            now = datetime.utcnow()
            time_diff = now - last_time
            
            days = time_diff.days
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            
            if days > 0:
                last_seen = f"{days}d"
            elif hours > 0:
                last_seen = f"{hours}h"
            else:
                last_seen = f"{minutes}m"
        else:
            last_seen = "N/A"
        
        # Format the event type with proper capitalization
        event_type = event['type'].capitalize() if event['type'] else 'Unknown'
        
        formatted_events.append({
            'type': event_type,
            'reason': event['reason'] or 'Unknown',
            'object': event['involved_object'] or 'Unknown',
            'message': event['message'] or 'No message',
            'count': event['count'] or 1,
            'last_seen': last_seen
        })
    
    return jsonify(formatted_events)

@api.route('/images/<namespace>')
@handle_kubernetes_errors
def get_images(namespace):
    """Get container images for a namespace"""
    pods = get_pods_in_namespace(namespace)
    image_data = []
    
    for pod in pods:
        images = get_pod_images(pod)
        for image in images:
            image_data.append({
                'pod_name': pod.metadata.name,
                'image': image
            })
    
    return jsonify(image_data)

@api.route('/images')
@handle_kubernetes_errors
def list_all_images():
    """Get container images from all namespaces"""
    pods = get_all_pods()
    image_data = []
    
    for pod in pods:
        images = get_pod_images(pod)
        for image in images:
            image_data.append({
                'namespace': pod.metadata.namespace,
                'pod_name': pod.metadata.name,
                'image': image.split(':')[1] if ':' in image else image
            })
    
    return jsonify(image_data)

@api.route('/namespaces')
@handle_kubernetes_errors
def list_namespaces():
    """Get list of all namespaces"""
    try:
        namespaces = get_namespaces()
        return jsonify(namespaces)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_age(timestamp):
    if not timestamp:
        return 'N/A'
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    age_delta = now - timestamp
    days = age_delta.days
    hours = age_delta.seconds // 3600
    minutes = (age_delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    return f"{minutes}m"


@api.route('/pods/<namespace>/<pod_name>')
@handle_kubernetes_errors
def get_pod_details(namespace, pod_name):
    """Get detailed information about a specific pod"""
    pods = get_pods_in_namespace(namespace)
    pod = next((p for p in pods if p.metadata.name == pod_name), None)
    
    if not pod:
        return jsonify({'error': 'Pod not found'}), 404
    
    # Get all pod details
    health = get_pod_health(pod)
    resources = get_pod_resources(pod)
    restart_count = get_pod_restart_count(pod)
    images = get_pod_images(pod)
    
    # Calculate age
    age = calculate_age(pod.metadata.creation_timestamp)
    
    # Get detailed status
    status = 'Unknown'
    if pod.status:
        status = pod.status.phase
        
        # Get container statuses
        container_statuses = []
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                container_status = {
                    'name': container.name,
                    'ready': container.ready,
                    'restarts': container.restart_count,
                    'image': container.image,
                }
                
                # Get current state
                if container.state.running:
                    container_status['state'] = 'Running'
                    container_status['started_at'] = container.state.running.started_at.strftime("%Y-%m-%d %H:%M:%S")
                elif container.state.waiting:
                    container_status['state'] = 'Waiting'
                    container_status['reason'] = container.state.waiting.reason
                    container_status['message'] = container.state.waiting.message
                elif container.state.terminated:
                    container_status['state'] = 'Terminated'
                    container_status['reason'] = container.state.terminated.reason
                    container_status['exit_code'] = container.state.terminated.exit_code
                
                container_statuses.append(container_status)
    
    # Format CPU and memory
    cpu = resources['cpu']['request']
    memory = resources['memory']['request']
    cpu_limit = resources['cpu']['limit']
    memory_limit = resources['memory']['limit']
    
    if cpu == '0':
        cpu = 'N/A'
    if memory == '0':
        memory = 'N/A'
    if cpu_limit == '0':
        cpu_limit = 'N/A'
    if memory_limit == '0':
        memory_limit = 'N/A'
    
    pod_details = {
        'name': pod.metadata.name,
        'namespace': namespace,
        'status': status,
        'health': health,
        'age': age,
        'created': pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else 'N/A',
        'labels': pod.metadata.labels or {},
        'node': pod.spec.node_name if pod.spec.node_name else 'N/A',
        'ip': pod.status.pod_ip if pod.status.pod_ip else 'N/A',
        'resources': {
            'cpu': {'request': cpu, 'limit': cpu_limit},
            'memory': {'request': memory, 'limit': memory_limit}
        },
        'containers': container_statuses,
        'images': images,
        'total_restarts': restart_count
    }
    
    return jsonify(pod_details)
