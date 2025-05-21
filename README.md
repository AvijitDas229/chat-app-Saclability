# Scalable Chat Application (Microservices Architecture)

This project is a **scalable chat application backend** built using **FastAPI**, **MongoDB**, **RabbitMQ**, **Docker**, and **NGINX**. It demonstrates real-world architecture patterns like **microservices decomposition**, **JWT-based authentication**, **asynchronous messaging**, and **reverse proxy routing**, with a focus on modularity and scalability.

---

## Architecture Overview

The application is organized as a set of independent services communicating over a Docker network. The key components include:

- **Auth-Service** – Handles user login and JWT token issuance
- **User-Service** – Manages user profile data and secure user-related APIs
- **Chat-Service** – Accepts messages from authenticated users and publishes them to RabbitMQ
- **Chat-Consumer** – Consumes messages from RabbitMQ and stores them in MongoDB
- **RabbitMQ** – Acts as a message broker for asynchronous communication
- **NGINX** – Serves as a reverse proxy and load balancer for routing HTTP traffic to appropriate services

---

## Technologies Used

| Component        | Stack / Tools                  |
|------------------|-------------------------------|
| API Framework    | FastAPI (Python)              |
| Database         | MongoDB                       |
| Authentication   | JWT Tokens                    |
| Messaging Queue  | RabbitMQ                      |
| Reverse Proxy    | NGINX                         |
| Containerization | Docker & Docker Compose       |

---

## Microservices

### Auth-Service
- Endpoint: `/auth/login`
- Accepts credentials, validates them, and returns a signed JWT
- Token includes user ID in the `sub` claim
- Stateless authentication system

### User-Service
- Endpoint: `/users/me`
- Requires a valid JWT token
- Fetches user details from the database
- JWT middleware validates access tokens

### Chat-Service
- Endpoint: `/chat/send`
- Accepts a message payload and JWT token
- Publishes messages to RabbitMQ via a producer
- Stateless and horizontally scalable

### Chat-Consumer
- Listens to RabbitMQ queue
- Persists incoming messages to MongoDB
- Operates as a background service

---

## Service Communication

- Services communicate over an internal Docker network
- All external requests are routed through **NGINX**
- JWT tokens are shared between services for stateless security
- RabbitMQ enables decoupling between producers (chat-service) and consumers (chat-consumer)

---

## Testing Strategy

- **JWT Validation**  
  Verified that access to protected routes is only allowed with valid tokens

- **API Testing (Postman)**  
  - `POST /auth/login` – Token issuance  
  - `GET /users/me` – Protected user data access  
  - `POST /chat/send` – Message publishing to RabbitMQ  

- **NGINX Routing**  
  Confirmed that `/auth`, `/users`, and `/chat` routes correctly proxy requests to their respective services

- **Horizontal Scalability**  
  Multiple chat-service containers were deployed to confirm stateless behavior and load balancing via NGINX

- **RabbitMQ Messaging**  
  Verified that messages published to RabbitMQ are reliably consumed and stored in MongoDB via the consumer service

---

## Conclusion

This project effectively showcases how containerized microservices, JWT-based security, reverse proxy routing, and asynchronous messaging via RabbitMQ can be integrated to build a **robust, modular, and scalable backend**. The decoupled design allows each service to evolve independently and handle increasing load with minimal coupling. The architecture is ready for further enhancement into a full-scale production-ready chat platform.
