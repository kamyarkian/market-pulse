# 1. Build Stage
FROM eclipse-temurin:17-jdk-jammy AS builder
WORKDIR /app

# Copy Maven wrapper and config first
COPY .mvn/ .mvn
COPY mvnw pom.xml ./

# --- THE FIX: Convert Windows line endings (CRLF) to Linux (LF) ---
# This line is the "Translation Layer" that fixes the issue.
RUN sed -i 's/\r$//' mvnw && chmod +x mvnw

# Pre-download dependencies
RUN ./mvnw dependency:go-offline

# Copy source code
COPY src ./src

# Build the application
RUN ./mvnw clean package -DskipTests

# 2. Run Stage
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]