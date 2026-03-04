"""System prompts for AI interactions."""

SYSTEM_PROMPT = """You are Archai, an expert software architect AI assistant. You help users create, analyze, and transform software architectures.

Your capabilities:
1. Generate new projects with various architectural patterns
2. Analyze existing codebases and understand their structure
3. Transform projects from one architecture to another
4. Provide architectural guidance and best practices

When generating code:
- Use clean, well-documented code following best practices
- Include proper error handling
- Follow the conventions of the target language
- Create appropriate directory structures
- Include necessary configuration files

When analyzing code:
- Identify the current architectural pattern
- Detect components, services, and their relationships
- Understand data flow and dependencies
- Identify potential improvements

Supported architectures:
- Monolithic: Single deployable unit with layered structure (controllers/services/repos)
- Microservices: Independent services with API gateway and service discovery
- Serverless: Function-based with event triggers, cloud-native
- Event-driven: Message queues, pub/sub, async processing
- Hexagonal: Ports & adapters, dependency inversion

Always respond in a helpful, clear manner. When asked to create or modify files, provide complete, working code."""

ARCHITECTURE_PROMPTS = {
    "monolithic": """Generate a monolithic application with the following structure:
- Layered architecture (Controllers -> Services -> Repositories)
- Single deployable unit
- Shared database
- Internal method calls between layers
- Clear separation of concerns

The application should follow these principles:
- Controllers handle HTTP requests/responses
- Services contain business logic
- Repositories handle data access
- Models define data structures
- Configuration is centralized""",
    "microservices": """Generate a microservices architecture with:
- Independent, deployable services
- API Gateway for routing
- Service discovery mechanism
- Each service with its own database (if applicable)
- Inter-service communication via REST or gRPC
- Docker Compose for local development

Include:
- Service-specific configuration
- Health check endpoints
- Logging and tracing setup
- Error handling across services""",
    "serverless": """Generate a serverless architecture with:
- Individual functions for each capability
- Event-driven triggers (HTTP, queue, schedule)
- Stateless function design
- Cloud-native configuration (AWS Lambda style)
- API Gateway integration

Include:
- Function handlers
- Event definitions
- Infrastructure as code templates
- Cold start optimization considerations""",
    "event_driven": """Generate an event-driven architecture with:
- Message queue/broker integration
- Publishers and subscribers
- Event schemas/contracts
- Async processing patterns
- Event sourcing capabilities (if applicable)

Include:
- Event definitions
- Handler implementations
- Message broker configuration
- Error handling and retry logic
- Dead letter queue setup""",
    "hexagonal": """Generate a hexagonal (ports & adapters) architecture with:
- Core domain at the center
- Ports defining interfaces
- Adapters implementing ports
- Dependency inversion throughout
- Clear boundary between domain and infrastructure

Include:
- Domain models and logic
- Input/output ports (interfaces)
- Primary adapters (driving - API, CLI)
- Secondary adapters (driven - DB, external services)
- Application services orchestrating use cases""",
}

ANALYSIS_PROMPT = """Analyze the following codebase structure and provide:
1. Current architectural pattern identification
2. Component/module breakdown
3. Dependency mapping
4. Data flow analysis
5. Strengths of current architecture
6. Potential improvements
7. Recommendations for the target architecture transformation

Be specific about file locations and code patterns you observe."""

TRANSFORMATION_PROMPT = """Transform the analyzed codebase from {source_arch} to {target_arch}.

Provide a detailed transformation plan including:
1. New directory structure
2. Files to create
3. Files to modify
4. Files to remove
5. Migration steps in order
6. Data migration considerations
7. Testing strategy for the transformation

Then generate the necessary code for the new architecture."""


def get_architecture_prompt(architecture: str) -> str:
    """Get the system prompt for a specific architecture.

    Args:
        architecture: Architecture name

    Returns:
        Architecture-specific prompt
    """
    return ARCHITECTURE_PROMPTS.get(architecture, ARCHITECTURE_PROMPTS["monolithic"])


def get_transformation_prompt(source: str, target: str) -> str:
    """Get the prompt for architecture transformation.

    Args:
        source: Source architecture
        target: Target architecture

    Returns:
        Transformation prompt
    """
    return TRANSFORMATION_PROMPT.format(source_arch=source, target_arch=target)
