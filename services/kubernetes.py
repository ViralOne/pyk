from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config import ConfigException
import logging
from datetime import datetime, timezone

# Initialize Kubernetes configuration
try:
    config.load_kube_config()
except ConfigException as e:
    logging.error(f"Error loading kubeconfig: {e}")
    logging.error("Make sure you have a valid kubeconfig file and kubectl is properly configured")

# Initialize the API client
v1 = client.CoreV1Api()
networking_v1 = client.NetworkingV1Api()

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

def get_namespace_resource_quotas(namespace):
    """Get resource quotas for a specific namespace"""
    try:
        quotas = v1.list_namespaced_resource_quota(namespace=namespace).items
        quota_data = []
        
        for quota in quotas:
            quota_data.append({
                'name': quota.metadata.name,
                'status': {
                    resource: {
                        'used': quota.status.used.get(resource, '0'),
                        'hard': quota.status.hard.get(resource, '0')
                    }
                    for resource in quota.status.hard.keys()
                }
            })
        
        return quota_data
    except ApiException as e:
        logging.error(f"Error getting resource quotas for namespace {namespace}: {e}")
        return []

def get_namespace_configmaps(namespace):
    """Get configmaps for a specific namespace"""
    try:
        configmaps = v1.list_namespaced_config_map(namespace=namespace).items
        configmap_data = []
        
        for cm in configmaps:
            age = (datetime.now(timezone.utc) - cm.metadata.creation_timestamp).days
            configmap_data.append({
                'name': cm.metadata.name,
                'data': cm.data or {},
                'age': f"{age}d" if age > 0 else "Today"
            })
        
        return configmap_data
    except ApiException as e:
        logging.error(f"Error getting configmaps for namespace {namespace}: {e}")
        return []

def get_namespace_secrets(namespace):
    """Get secrets for a specific namespace"""
    try:
        secrets = v1.list_namespaced_secret(namespace=namespace).items
        secret_data = []
        
        for secret in secrets:
            age = (datetime.now(timezone.utc) - secret.metadata.creation_timestamp).days
            secret_data.append({
                'name': secret.metadata.name,
                'type': secret.type,
                'age': f"{age}d" if age > 0 else "Today"
            })
        
        return secret_data
    except ApiException as e:
        logging.error(f"Error getting secrets for namespace {namespace}: {e}")
        return []

def get_namespace_services(namespace):
    """Get services for a specific namespace"""
    try:
        services = v1.list_namespaced_service(namespace=namespace).items
        service_data = []
        
        for svc in services:
            age = (datetime.now(timezone.utc) - svc.metadata.creation_timestamp).days
            ports = []
            
            if svc.spec.ports:
                for port in svc.spec.ports:
                    ports.append({
                        'port': port.port,
                        'targetPort': port.target_port,
                        'protocol': port.protocol
                    })
            
            external_ip = None
            if svc.status.load_balancer.ingress:
                external_ip = svc.status.load_balancer.ingress[0].ip
            
            service_data.append({
                'name': svc.metadata.name,
                'type': svc.spec.type,
                'clusterIP': svc.spec.cluster_ip,
                'externalIP': external_ip,
                'ports': ports,
                'age': f"{age}d" if age > 0 else "Today"
            })
        
        return service_data
    except ApiException as e:
        logging.error(f"Error getting services for namespace {namespace}: {e}")
        return []

def get_namespace_ingresses(namespace):
    """Get ingresses for a specific namespace"""
    try:
        ingresses = networking_v1.list_namespaced_ingress(namespace=namespace).items
        ingress_data = []
        
        for ing in ingresses:
            age = (datetime.now(timezone.utc) - ing.metadata.creation_timestamp).days
            
            # Process rules
            rules = []
            if ing.spec.rules:
                for rule in ing.spec.rules:
                    rule_data = {
                        'host': rule.host,
                        'paths': []
                    }
                    if rule.http and rule.http.paths:
                        for path in rule.http.paths:
                            rule_data['paths'].append({
                                'path': path.path,
                                'pathType': path.path_type,
                                'service': {
                                    'name': path.backend.service.name,
                                    'port': path.backend.service.port.number
                                } if path.backend.service else None
                            })
                    rules.append(rule_data)
            
            # Get TLS info
            tls = []
            if ing.spec.tls:
                for tls_item in ing.spec.tls:
                    tls.append({
                        'hosts': tls_item.hosts,
                        'secretName': tls_item.secret_name
                    })
            
            # Get ingress class name
            ingress_class = ing.spec.ingress_class_name if ing.spec.ingress_class_name else 'default'
            
            # Get address
            address = None
            if ing.status.load_balancer.ingress:
                address = ing.status.load_balancer.ingress[0].ip or ing.status.load_balancer.ingress[0].hostname
            
            ingress_data.append({
                'name': ing.metadata.name,
                'class': ingress_class,
                'rules': rules,
                'tls': tls,
                'address': address,
                'age': f"{age}d" if age > 0 else "Today"
            })
        
        return ingress_data
    except ApiException as e:
        logging.error(f"Error getting ingresses for namespace {namespace}: {e}")
        return []
