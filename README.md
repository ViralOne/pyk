### Pik
The project was created just to learn Python with Kubernetes modules

## Start server
`python3 ./app.py`

## URL Paths
| Path | Notes |
|---|---|
| `/health/<NAMESPACE>` | Check pods health from a namespace |
| `/images/<NAMESPACE>` | Check docker image tags from a specific namespace |
| `/images` | Show all docker image tags from all namespaces |
