# ════════════════════════════════════════════════════
#  LotoMind Enterprise — Java Backend (Multi-stage)
# ════════════════════════════════════════════════════

# ── Stage 1: Build ──────────────────────────────────
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

# ── Stage 2: Runtime ────────────────────────────────
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

RUN addgroup -S lotomind && adduser -S lotomind -G lotomind
COPY --from=build /build/target/*.jar app.jar
RUN chown -R lotomind:lotomind /app

USER lotomind
EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
