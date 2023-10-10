# URLShortener


//local
docker build -t my-postgres-db -f workerDockerfile .
docker run -d --name postgres-container my-postgres-db

docker build -t url_shortener -f Dockerfile .
docker run -d --name django-app-container -p 8000:8000 --link postgres-container:db url_shortener


// ec2
sudo docker build -t url_shortener -f Dockerfile .
docker run -d --name django-app-container -p 8000:8000 url_shortener

sudo aws ecr get-login-password --region ap-south-1 | sudo docker login --username AWS --password-stdin 524121514696.dkr.ecr.ap-south-1.amazonaws.com
sudo docker tag url_shortener:latest 524121514696.dkr.ecr.ap-south-1.amazonaws.com/urlshortener:latest

