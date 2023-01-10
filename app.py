from flask import Flask, request, render_template
from kubernetes import client, config

app = Flask(__name__)

# Load the Kubernetes configuration
config.load_kube_config()

# Create a Kubernetes API client
v1 = client.CoreV1Api()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get the list of namespaces
    namespaces = v1.list_namespace().items
    namespaces = [ns.metadata.name for ns in namespaces]
    
    if request.method == 'POST':
        # Get the selected namespace and list of pods in that namespace
        namespace = request.form['namespace']
        pods = v1.list_namespaced_pod(namespace=namespace).items
        
        # Get the docker image for each pod
        pod_images = []
        for pod in pods:
            image = pod.spec.containers[0].image
            
            # Rule the image was created for ECR remove all the details about the ECR URL and show only the tag
            if (image.__contains__("amazon")):
                parts = image.split(':')
                image_filtered = parts[1]
            else:
                image_filtered = image
            pod_images.append(image_filtered)
        
        # Render the template with the list of namespaces and images
        return render_template('index.html', namespaces=namespaces, namespace=namespace, pods=pods, pod_images=pod_images)
    else:
        # Render the template with an empty list of images
        return render_template('index.html', namespaces=namespaces, pod_images=[])

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
