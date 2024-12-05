from flask import Blueprint, jsonify
from services.kubernetes import (
    get_pods_in_namespace, get_pod_health, get_pod_resources,
    get_pod_images, get_pod_restart_count, get_namespace_events,
    get_all_pods
)

api = Blueprint('api', __name__)

@api.route('/pods/<namespace>')
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
            'age': pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else 'Unknown',
            'restarts': restart_count
        })
    
    return jsonify(pod_data)

@api.route('/events/<namespace>')
def get_events(namespace):
    """Get events for a namespace"""
    events = get_namespace_events(namespace)
    return jsonify(events)

@api.route('/images/<namespace>')
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
