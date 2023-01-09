### Pik

## Start server
`python3 ./app.py`

## URL Paths
Check pods health in a namespace: `http://127.0.0.1:5000/health/<NAMESPACE>`

Check docker image tags in a specific namespace: `http://127.0.0.1:5000/images/<NAMESPACE>`

Check docker image tags in all namespaces: `http://127.0.0.1:5000/images`
