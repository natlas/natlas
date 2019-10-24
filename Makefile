NS_IMAGE_NAME=natlas-server
NA_IMAGE_NAME=natlas-agent

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean: ## Delete all images and clean up running containers related to natlas
	docker-compose stop && docker-compose rm -f
	docker rmi ${NA_IMAGE_NAME} || true
	docker rmi ${NS_IMAGE_NAME} || true

clean-volumes: clean ## Delete all volumes, images and clean up running containers related to natlas
	docker volume rm natlas_elastic
	docker volume rm natlas_ns-data

create-account: ## Creates admin account with email admin@admin.local password will be in output
	docker-compose exec natlas-server python3 add-user.py --admin admin@admin.local

add-scopes: ## Adds scopes from myscopefile.txt 
	docker-compose exec natlas-server python3 add-scope.py --scope /myscopefile.txt --verbose

build: ## Build containers
	cd natlas-agent && docker build -t ${NA_IMAGE_NAME} . && cd -
	cd natlas-server && docker build -t ${NS_IMAGE_NAME} . && cd -

gen-cert: ## Generate certs for the container
	openssl ecparam -name secp384r1 -genkey -noout -out dev-key.key
	openssl req -new -batch -x509 -days 3652 -key dev-key.key -out dev-cert.crt

run: build gen-cert ## Builds and runs containers
	docker-compose up -d elastic
	sleep 10
	docker-compose up -d natlas-server
	sleep 10
	docker-compose up -d natlas-agent

get-logs: ## Gets the logs
	docker-compose logs --tail 100
