# nginx

Sets up the NGINX development server for the dev environment. We use nginx in the dev environment as a reverse proxy to simulate the production environment. In the production environment, an instance of API Management routes requests to AKS PQE services with a path prefix. That path prefix needs to be stripped by the nginx ingress controller, and the nginx reverse proxy mimics this in the development environment.

Credit to https://github.com/azavea/pfb-network-connectivity/tree/develop/src/nginx

