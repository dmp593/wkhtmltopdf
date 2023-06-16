requirements:
	pdm export -f requirements --without-hashes > requirements.txt

up: requirements
	docker-compose up -d

down:
	docker-compose down --rmi local --volumes
	docker builder prune -f
	rm -rf requirements.txt

bash:
	docker-compose exec -it app bash