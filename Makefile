# 🔨 CodeForge Agents — common commands
.PHONY: install ingest run test docker-build docker-run k8s-deploy

install:        ## install dependencies into the current environment
	pip install -r requirements.txt

ingest:         ## (re)build the knowledge index
	python -m rag.ingest

run:            ## start the app locally
	streamlit run app.py

test:           ## run the unit tests (no API key needed)
	python tests/test_all.py

docker-build:   ## build the production image (index baked in)
	docker build -t codeforge-agents:4.3 .

docker-run:     ## run the image; key comes from your shell or .env
	docker run -p 8501:8501 --env-file .env codeforge-agents:4.3

k8s-deploy:     ## deploy to the current kubectl context
	kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
