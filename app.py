from flask import Flask, render_template
from kubernetes import client, config

app = Flask(__name__)

# Load the Kubernetes configuration
config.load_kube_config()

# Create a Kubernetes API client
v1 = client.CoreV1Api()

@app.route('/')
def main():
  # Render the HTML page with all the routes
  return render_template('index.html')

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

@app.route('/images/<namespace>')
def get_image(namespace):
  # List all pods in the specified namespace
  pod_image = v1.list_namespaced_pod(namespace=namespace)

  # Extract the pod name and Docker image for each pod
  images = []
  for pod_image in pod_image.items:
    container = pod_image.spec.containers[0]
    images.append({
      'pod_name': pod_image.metadata.name,
      'image': container.image,
    })

  # Render the HTML page with the image
  return render_template('pod.html', namespace=namespace, images=images)

@app.route("/health/<namespace>")
def health(namespace):
    # List all pods in the specified namespace
    health = v1.list_namespaced_pod(namespace).items

    # For each pod, check its status and determine whether it is healthy or unhealthy
    health_info = []
    for pod in health:
        if pod.status.container_statuses:
            health = "healthy"
            for container_status in pod.status.container_statuses:
                if not container_status.ready:
                    health = "unhealthy"
                    break
        else:
            health = "unknown"
        health_info.append({
            "name": pod.metadata.name,
            "health": health
        })
    return render_template("health.html", namespace=namespace, pod_info=health_info)

if __name__ == '__main__':
  app.run()
