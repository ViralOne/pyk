from datetime import datetime, timedelta
from services.kubernetes import get_all_pods
from kubernetes import client, config
from kubernetes.client import ApiClient
import json

def format_cpu(cpu_str):
    """Convert Kubernetes CPU string to cores"""
    if not cpu_str:
        return 0
    
    try:
        # Handle millicores (e.g., '100m')
        if isinstance(cpu_str, str) and cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        # Handle direct core values
        return float(cpu_str)
    except (ValueError, AttributeError):
        return 0

def format_memory(memory_str):
    """Convert Kubernetes memory string to GB"""
    if not memory_str:
        return 0
    
    try:
        # Remove Ki, Mi, Gi suffix and convert to GB
        if memory_str.endswith('Ki'):
            return int(memory_str[:-2]) / (1024 * 1024)
        elif memory_str.endswith('Mi'):
            return int(memory_str[:-2]) / 1024
        elif memory_str.endswith('Gi'):
            return int(memory_str[:-2])
        else:
            return int(memory_str) / (1024 * 1024 * 1024)
    except (ValueError, AttributeError):
        return 0

def get_cluster_stats():
    """Get cluster statistics including node and pod counts, CPU and memory usage"""
    try:
        # Load kube config
        config.load_kube_config()
        v1 = client.CoreV1Api()
        
        # Get nodes
        nodes_list = v1.list_node()
        nodes = nodes_list.items
        node_count = len(nodes)
        
        # Get pods
        pods_list = v1.list_pod_for_all_namespaces()
        pods = pods_list.items
        current_pod_count = len(pods)
        
        # Calculate pod growth (simulated for now)
        previous_pod_count = int(current_pod_count * 0.95)  # Simulating 5% increase
        pod_growth = ((current_pod_count - previous_pod_count) / previous_pod_count * 100) if previous_pod_count > 0 else 0
        
        # Calculate resource usage
        total_cpu_capacity = 0
        total_cpu_used = 0
        total_memory_capacity = 0
        total_memory_used = 0
        ready_nodes = 0
        
        for node in nodes:
            # Check if node is ready
            for condition in node.status.conditions:
                if condition.type == 'Ready':
                    if condition.status == 'True':
                        ready_nodes += 1
                    break
            
            # Get node capacity
            allocatable = node.status.allocatable
            total_cpu_capacity += format_cpu(allocatable.get('cpu', '0'))
            total_memory_capacity += format_memory(allocatable.get('memory', '0'))
        
        # Calculate pod resource usage
        for pod in pods:
            if pod.status.phase == 'Running':
                for container in pod.spec.containers:
                    resources = container.resources
                    if resources.requests:
                        cpu_request = resources.requests.get('cpu', '0')
                        memory_request = resources.requests.get('memory', '0')
                        total_cpu_used += format_cpu(cpu_request)
                        total_memory_used += format_memory(memory_request)
        
        # Calculate percentages
        node_usage = (ready_nodes / node_count * 100) if node_count > 0 else 0
        cpu_usage = (total_cpu_used / total_cpu_capacity * 100) if total_cpu_capacity > 0 else 0
        memory_usage = (total_memory_used / total_memory_capacity * 100) if total_memory_capacity > 0 else 0
        
        stats = {
            'node_count': node_count,
            'node_usage': round(node_usage, 1),
            'pod_count': current_pod_count,
            'pod_growth': round(pod_growth, 1),
            'cpu_usage': round(cpu_usage, 1),
            'memory_usage': round(memory_usage, 1),
            'total_cpu': round(total_cpu_capacity, 1),
            'total_memory': round(total_memory_capacity, 1),
            'used_cpu': round(total_cpu_used, 1),
            'used_memory': round(total_memory_used, 1)
        }
        
        return stats
        
    except Exception as e:
        print(f"Error getting cluster stats: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full stack trace
        return {
            'node_count': 0,
            'node_usage': 0,
            'pod_count': 0,
            'pod_growth': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'total_cpu': 0,
            'total_memory': 0,
            'used_cpu': 0,
            'used_memory': 0
        }
