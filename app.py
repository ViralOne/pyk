import os
import subprocess

from flask import Flask, render_template
from kubernetes import client, config

app = Flask(__name__)

# Load the Kubernetes configuration
config.load_kube_config()

# Create a Kubernetes API client
v1 = client.CoreV1Api()

@app.route('/images')
def list_images():
  # List all pods in all namespaces
  pods = v1.list_pod_for_all_namespaces(watch=False)

  # Extract the namespace, pod name, and Docker image for each pod
  images = []
  for pod in pods.items:
    container = pod.spec.containers[0]
    images.append({
      'namespace': pod.metadata.namespace,
      'pod_name': pod.metadata.name,
      'image': container.image,
    })

  # Render the HTML page with the list of images
  return render_template('images.html', images=images)

@app.route("/health/<namespace>")
def pods(namespace):
    # List all pods in the specified namespace
    pods = v1.list_namespaced_pod(namespace).items

    # For each pod, check its status and determine whether it is healthy or unhealthy
    pod_info = []
    for pod in pods:
        if pod.status.container_statuses:
            health = "healthy"
            for container_status in pod.status.container_statuses:
                if not container_status.ready:
                    health = "unhealthy"
                    break
        else:
            health = "unknown"
        pod_info.append({
            "name": pod.metadata.name,
            "health": health
        })
    return render_template("health.html", namespace=namespace, pod_info=pod_info)

if __name__ == '__main__':
  app.run()
