FROM eclipse-temurin:21-jdk AS build
WORKDIR /game
COPY src/main/java src/main/java
COPY web web
RUN mkdir classes && javac --release 17 -encoding UTF-8 -d classes src/main/java/sanga/*.java && jar --create --file game.jar --main-class sanga.Server -C classes . web

FROM eclipse-temurin:21-jre
WORKDIR /game
COPY --from=build /game/game.jar .
ENV GAME_HOST=0.0.0.0
ENTRYPOINT ["java", "-jar", "game.jar"]
