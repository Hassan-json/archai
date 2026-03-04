# Microservices Architecture

This project demonstrates a microservices architecture for a simple Hello World application.

## Services
- **Hello Service**: Responds with a hello message.
- **API Gateway**: Routes requests to the Hello Service.

## Running the Application
1. Ensure Docker and Docker Compose are installed on your machine.
2. Navigate to the project directory.
3. Run `docker-compose up` to start the services.
4. Access the API Gateway at `http://localhost:5000/hello` to receive the hello message.

## Directory Structure
- /hello_service: Contains the Hello Service.
- /api_gateway: Contains the API Gateway.