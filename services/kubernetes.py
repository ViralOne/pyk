from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config import ConfigException
import logging

# Initialize Kubernetes configuration
try:
    config.load_kube_config()
except ConfigException as e:
    logging.error(f"Error loading kubeconfig: {e}")
    logging.error("Make sure you have a valid kubeconfig file and kubectl is properly configured")

# Initialize the API client
v1 = client.CoreV1Api()

def get_namespaces():
    """Get list of all namespaces"""
    try:
        namespaces = v1.list_namespace().items
        return [ns.metadata.name for ns in namespaces]
    except ApiException as e:
        logging.error(f"Error getting namespaces: {e}")
        return []

def get_pods_in_namespace(namespace):
    """Get all pods in a specific namespace"""
    try:
        return v1.list_namespaced_pod(namespace=namespace).items
    except ApiException as e:
        logging.error(f"Error getting pods in namespace {namespace}: {e}")
        return []

def get_all_pods():
    """Get pods from all namespaces"""
    try:
        return v1.list_pod_for_all_namespaces().items
    except ApiException as e:
        logging.error(f"Error getting pods from all namespaces: {e}")
        return []

def get_pod_resources(pod):
    """Extract resource requests and limits from a pod"""
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

def get_pod_health(pod):
    """Determine pod health status"""
    status = pod.status
    health = 'unknown'
    
    if status and status.container_statuses:
        all_ready = all(container.ready for container in status.container_statuses)
        all_running = all(container.state.running for container in status.container_statuses)
        
        if all_ready and all_running:
            health = 'healthy'
        elif not all_ready or not all_running:
            health = 'unhealthy'
    
    return health

def get_pod_images(pod):
    """Get container images from a pod"""
    if pod.spec.containers:
        return [container.image for container in pod.spec.containers]
    return []

def get_pod_restart_count(pod):
    """Get total restart count for a pod"""
    if pod.status and pod.status.container_statuses:
        return sum(container.restart_count for container in pod.status.container_statuses)
    return 0

def get_namespace_events(namespace):
    """Get events for a specific namespace"""
    try:
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
        
        return sorted(event_data, key=lambda x: x['last_timestamp'] if x['last_timestamp'] else '', reverse=True)
    except ApiException as e:
        logging.error(f"Error getting events for namespace {namespace}: {e}")
        return []
