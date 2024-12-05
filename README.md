### Pik
The project was created just to learn Python with Kubernetes modules

## Start server
`python3 ./app.py`

## Available Endpoints

| Service Name | Path | Type | Description |
|---|---|---|---|
| Overview Dashboard | `/` | UI | Main dashboard with cluster overview |
| Images Overview | `/images` | UI | View all Docker images across namespaces |
| Namespace Details | `/namespace/<NAMESPACE>` | UI | Combined view with pod details, health status, images, and events |
| Pod Details API | `/api/pods/<NAMESPACE>/<POD_NAME>` | JSON API | Get detailed information about a specific pod |
| Pod Health API | `/api/health/<NAMESPACE>` | JSON API | Get health status of pods in namespace |
| Docker Images API | `/api/images` | JSON API | Get all Docker images |
| Docker Images by Namespace API | `/api/images/<NAMESPACE>` | JSON API | Get Docker images in namespace |
| Events API | `/api/events/<NAMESPACE>` | JSON API | Get events for namespace |
