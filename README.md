# Dutch Gas prices API
## Returns Euro 95 and Diesel prices from directlease.nl

To run your own Dutch Gas prices API.
Background: https://community.home-assistant.io/t/dutch-gas-priceses/59230

### Build & Deploy
##### Docker
As this Python application requires some external dependancies like Tesseract, the most easy way is to run it as a Docker container:
```
1 - Download or clone this reposistory to a docker machine
2 - Goto the main folder (where the docker file is located)
3 - docker build -t gaspricesapi .
4 - docker stop gaspricesapi && docker rm gaspricesapi
5 - docker run -d --name=gaspricesapi -p 5035:5035/tcp gaspricesapi:latest
Or, if you want to keep your cache on the host machine:
5 - docker run -d --name=gaspricesapi -p 5035:5035/tcp -v /your/host/folder/here:/home/apiuser/app/cache gaspricesapi:latest
```