from flask import Blueprint, jsonify, request
from functools import wraps
from kubernetes import client, config
from services.kubernetes import (
    get_pods_in_namespace, get_pod_health, get_pod_resources,
    get_pod_images, get_pod_restart_count, get_namespace_events,
    get_all_pods, get_namespaces, get_namespace_resource_quotas,
    get_namespace_configmaps, get_namespace_secrets, get_namespace_services,
    get_namespace_ingresses
)

api = Blueprint('api', __name__)
v1 = client.CoreV1Api()
networking_v1 = client.NetworkingV1Api()

def handle_kubernetes_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except client.rest.ApiException as e:
            if e.status == 403:
                return jsonify({'error': 'Access forbidden. Check RBAC permissions.'}), 403
            elif e.status == 404:
                return jsonify({'error': 'Resource not found.'}), 404
            return jsonify({'error': f'Kubernetes API error: {str(e)}'}), e.status or 500

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
                'image': image.split('/')[-1].split(':')[1] if ':' in image.split('/')[-1] else image
            })
    
    return jsonify(image_data)

@api.route('/namespaces')
@handle_kubernetes_errors
def list_namespaces():
    """Get list of all namespaces"""
    namespaces = get_namespaces()
    return jsonify(namespaces)

@api.route('/quotas/<namespace>')
@handle_kubernetes_errors
def get_quotas(namespace):
    """Get resource quotas for a namespace"""
    quotas = get_namespace_resource_quotas(namespace)
    return jsonify(quotas)

@api.route('/configmaps/<namespace>')
@handle_kubernetes_errors
def get_configmaps(namespace):
    """Get configmaps for a namespace"""
    configmaps = get_namespace_configmaps(namespace)
    return jsonify(configmaps)

@api.route('/secrets/<namespace>')
@handle_kubernetes_errors
def get_secrets(namespace):
    """Get secrets for a namespace"""
    secrets = get_namespace_secrets(namespace)
    return jsonify(secrets)

@api.route('/services/<namespace>')
@handle_kubernetes_errors
def get_services(namespace):
    """Get services for a namespace"""
    services = get_namespace_services(namespace)
    return jsonify(services)

@api.route('/ingresses/<namespace>')
@handle_kubernetes_errors
def get_ingresses(namespace):
    """Get ingresses for a namespace"""
    ingresses = get_namespace_ingresses(namespace)
    return jsonify(ingresses)

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

@api.route('/debug/<resource_type>/<namespace>/<name>')
@handle_kubernetes_errors
def debug_resource(resource_type, namespace, name):
    try:
        # Get the main resource details
        resource_details = {}
        events = []
        related_resources = {}
        
        if resource_type == 'configmap':
            resource = v1.read_namespaced_config_map(name, namespace)
            resource_details = {
                'type': 'ConfigMap',
                'name': resource.metadata.name,
                'data_keys': list(resource.data.keys()) if resource.data else [],
                'created': resource.metadata.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            # Find pods using this configmap
            pods = v1.list_namespaced_pod(namespace).items
            related_resources['Pods'] = []
            for pod in pods:
                uses_configmap = False
                for volume in pod.spec.volumes or []:
                    if volume.config_map and volume.config_map.name == name:
                        uses_configmap = True
                        break
                for container in pod.spec.containers:
                    for env in container.env or []:
                        if env.value_from and env.value_from.config_map_key_ref and env.value_from.config_map_key_ref.name == name:
                            uses_configmap = True
                            break
                if uses_configmap:
                    related_resources['Pods'].append({
                        'name': pod.metadata.name,
                        'status': 'Healthy' if pod.status.phase == 'Running' else pod.status.phase,
                        'info': f'Using ConfigMap in {"volume" if volume else "environment"}'
                    })
                    
        elif resource_type == 'secret':
            resource = v1.read_namespaced_secret(name, namespace)
            resource_details = {
                'type': 'Secret',
                'name': resource.metadata.name,
                'secret_type': resource.type,
                'data_keys': list(resource.data.keys()) if resource.data else [],
                'created': resource.metadata.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            # Find pods and ingresses using this secret
            pods = v1.list_namespaced_pod(namespace).items
            related_resources['Pods'] = []
            for pod in pods:
                uses_secret = False
                for volume in pod.spec.volumes or []:
                    if volume.secret and volume.secret.secret_name == name:
                        uses_secret = True
                        break
                for container in pod.spec.containers:
                    for env in container.env or []:
                        if env.value_from and env.value_from.secret_key_ref and env.value_from.secret_key_ref.name == name:
                            uses_secret = True
                            break
                if uses_secret:
                    related_resources['Pods'].append({
                        'name': pod.metadata.name,
                        'status': 'Healthy' if pod.status.phase == 'Running' else pod.status.phase,
                        'info': f'Using Secret in {"volume" if volume else "environment"}'
                    })
            
            ingresses = networking_v1.list_namespaced_ingress(namespace).items
            related_resources['Ingresses'] = []
            for ingress in ingresses:
                if ingress.spec.tls:
                    for tls in ingress.spec.tls:
                        if tls.secret_name == name:
                            related_resources['Ingresses'].append({
                                'name': ingress.metadata.name,
                                'status': 'Active',
                                'info': 'Using Secret for TLS'
                            })
                            
        elif resource_type == 'service':
            resource = v1.read_namespaced_service(name, namespace)
            resource_details = {
                'name': resource.metadata.name,
                'type': resource.spec.type,
                'cluster_ip': resource.spec.cluster_ip,
                'ports': [f"{port.port}:{port.target_port}/{port.protocol}" for port in resource.spec.ports],
                'created': resource.metadata.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Find pods this service targets
            pods = v1.list_namespaced_pod(namespace).items
            related_resources['Pods'] = []
            selector = resource.spec.selector
            if selector:
                for pod in pods:
                    if all(pod.metadata.labels.get(k) == v for k, v in selector.items()):
                        related_resources['Pods'].append({
                            'name': pod.metadata.name,
                            'status': 'Healthy' if pod.status.phase == 'Running' else pod.status.phase,
                            'info': 'Targeted by Service'
                        })
            
            # Find ingresses using this service
            ingresses = networking_v1.list_namespaced_ingress(namespace).items
            related_resources['Ingresses'] = []
            for ingress in ingresses:
                for rule in ingress.spec.rules or []:
                    for path in rule.http.paths:
                        if path.backend.service and path.backend.service.name == name:
                            related_resources['Ingresses'].append({
                                'name': ingress.metadata.name,
                                'status': 'Active',
                                'info': f'Routing to Service via {rule.host}{path.path}'
                            })
                            
        elif resource_type == 'ingress':
            resource = networking_v1.read_namespaced_ingress(name, namespace)
            resource_details = {
                'type': 'Ingress',
                'name': resource.metadata.name,
                'class': resource.spec.ingress_class_name,
                'hosts': [rule.host for rule in resource.spec.rules],
                'created': resource.metadata.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Find related services
            related_resources['Services'] = []
            for rule in resource.spec.rules or []:
                for path in rule.http.paths:
                    if path.backend.service:
                        service_name = path.backend.service.name
                        try:
                            service = v1.read_namespaced_service(namespace, service_name)
                            related_resources['Services'].append({
                                'name': service.metadata.name,
                                'status': 'Active',
                                'info': f'Targeted via {rule.host}{path.path}'
                            })
                        except client.rest.ApiException as e:
                            related_resources['Services'].append({
                                'name': service_name,
                                'status': 'Error',
                                'info': f'Service not found: {str(e)}'
                            })
            
            # Find TLS secrets
            if resource.spec.tls:
                related_resources['Secrets'] = []
                for tls in resource.spec.tls:
                    try:
                        secret = v1.read_namespaced_secret(namespace, tls.secret_name)
                        related_resources['Secrets'].append({
                            'name': secret.metadata.name,
                            'status': 'Active',
                            'info': f'TLS Secret for {", ".join(tls.hosts)}'
                        })
                    except client.rest.ApiException as e:
                        related_resources['Secrets'].append({
                            'name': tls.secret_name,
                            'status': 'Error',
                            'info': f'Secret not found: {str(e)}'
                        })
        
        # Get events for the resource
        field_selector = f"involvedObject.name={name},involvedObject.namespace={namespace}"
        events_list = v1.list_namespaced_event(namespace, field_selector=field_selector).items
        for event in events_list:
            if event.involved_object.kind.lower() == resource_type:
                events.append({
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'count': event.count,
                    'first_timestamp': event.first_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_timestamp': event.last_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return jsonify({
            'type': resource_details.get('type', resource_type.title()),
            'name': name,
            'details': resource_details,
            'events': events,
            'related': related_resources
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/get-contexts')
def get_contexts():
    """Get list of available Kubernetes contexts"""
    contexts, _ = config.list_kube_config_contexts()
    return jsonify({'contexts': [context['name'] for context in contexts]})

@api.route('/set-context/<context_name>', methods=['POST'])
def set_context(context_name):
    try:
        config.load_kube_config(context=context_name)
        return jsonify({'success': True})
    except config.ConfigException as e:
        return jsonify({'success': False, 'error': str(e)}), 500
