# Auto-Extraction Service

A production-ready microservice that handles intelligent data extraction and parsing tasks for document analysis pipelines using RabbitMQ messaging and AI-powered agents.

## Overview

The auto-extraction service provides intelligent document processing capabilities:
- **Address Parsing**: Uses LLM-powered agents to parse and structure address information
- **Key-Value Extraction**: Intelligent extraction of structured data from unstructured documents
- **Dimension Parsing**: Extracts and formats dimensional data from documents
- **Data Exception Handling**: Resolves and processes data quality issues
- **LLM Integration**: Leverages large language models for intelligent parsing

## Features

### 🏠 Address Parsing Agent
- Uses LLM models for intelligent address parsing
- Supports complex address structures with sub-components
- Handles contact information extraction (name, phone, email)
- Fuzzy matching for address field identification

### 🔑 Key-Value Extraction
- Intelligent key-value pair extraction from documents
- Profile-based mapping and validation
- Support for complex nested data structures
- Label mapping with qualifier support

### 📏 Dimension Parser
- Extracts dimensional data from documents
- Supports various measurement formats
- Validates and normalizes dimension values

### 🛠️ Data Exception Resolution
- Handles data quality issues automatically
- KV exception resolution with intelligent mapping
- Label exception processing
- Data validation and correction

### 🤖 LLM Integration
- Multiple LLM client support
- Structured result generation
- Format standardization
- Configurable model parameters

## Architecture

### Project Structure
```
auto-extraction/
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── intelligent_parsers_module/     # AI-powered parsing agents
│   ├── address_parser_agent.py    # Address parsing with LLM
│   ├── dimension_parser_agent.py  # Dimension extraction
│   └── intelligent_parsers_factory.py # Parser factory
│
├── rabbitmq/                       # Message queue infrastructure
│   ├── consumer.py                # Message consumer (main worker)
│   ├── handler.py                 # Task implementations
│   └── __init__.py
│
├── utils/                          # Shared utilities
│   └── config.py                  # Configuration management
│
├── value_conversion_module/        # Data conversion utilities
└── cdz_data_modification_agents/   # Data modification agents
```

### Components
- **Intelligent Parsers**: AI-powered agents for document parsing
- **RabbitMQ Workers**: Asynchronous message processing
- **Utils**: Shared utilities and configuration
- **LLM Clients**: Integration with various LLM providers

### Message Flow
1. Backend service publishes message to `to_extraction` queue
2. Auto-extraction worker consumes message and routes to appropriate handler
3. Handler calls intelligent parsers for document processing
4. Results are formatted and structured
5. Response message is published back to `to_pipeline` queue
6. Backend service consumes response and continues processing

## RabbitMQ Message Types

### Extraction Tasks
Publish message to `to_extraction` queue with message type `extraction`:

```json
{
  "document_path": "/path/to/document.json",
  "job_id": "aidb:job:abc123:batch001",
  "batch_id": "batch-123",
  "extraction_type": "address_parsing",
  "service_identifier": "auto-extraction"
}
```

Response is published back to `to_pipeline` queue with message type `extraction_response`:

```json
{
  "status_code": 200,
  "job_id": "aidb:job:abc123:batch001",
  "batch_id": "batch-123",
  "extracted_data": {},
  "service_identifier": "auto-extraction"
}
```

## Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest

# Queue Names
QUEUE_TO_EXTRACTION=to_extraction

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4

# Logging
LOG_LEVEL=INFO
```

### Configuration Management
All configuration is handled through environment variables with:
- Type hints for all settings
- Default values for development
- Validation on startup

## Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis and RabbitMQ
docker-compose up -d redis rabbitmq

# Run worker
python rabbitmq/consumer.py
```

## Monitoring

### Health Checks
- Worker status: Check RabbitMQ management console (http://localhost:15672)
- Redis connection: Verify Redis health
- LLM connectivity: Check API key and endpoint access

### Logging
- **Structured Logging**: All logs use Python's logging module
- **Log Levels**: DEBUG, INFO, WARNING, ERROR (configurable via `LOG_LEVEL`)
- **Application logs**: `docker logs extraction-worker`
- **Error tracking**: Structured error logging with exception tracebacks

### Performance Metrics
- Message processing time
- Queue depth monitoring
- Worker resource usage
- LLM API response times
- Redis connection health

## Performance

### Optimization
- **LLM Caching**: Response caching for repeated queries
- **Batch Processing**: Efficient handling of multiple documents
- **Message Queuing**: Asynchronous processing with RabbitMQ
- **Connection Pooling**: Optimized LLM client connections

### Scaling
- **Horizontal Scaling**: Multiple worker containers
- **Resource Management**: Configurable memory and CPU limits
- **Queue Management**: RabbitMQ message routing and priorities
- **Load Balancing**: RabbitMQ distributes messages automatically

## Troubleshooting

### Common Issues

#### LLM API Errors
```bash
# Check API key validity
export LLM_API_KEY=your_valid_key

# Test LLM connectivity
curl -H "Authorization: Bearer $LLM_API_KEY" https://api.openai.com/v1/models
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli -h redis ping
```

#### RabbitMQ Connection Issues
```bash
# Test RabbitMQ connection
rabbitmq-diagnostics -q ping

# Check queue status
rabbitmqctl list_queues
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python rabbitmq/consumer.py
```

## Integration

### Message Queue Integration
The auto-extraction service integrates with the main pipeline via RabbitMQ:
- **to_extraction**: Queue for incoming extraction tasks
- **to_pipeline**: Queue for processing results and responses
- **Message Types**: `extraction`
- **Response Types**: `extraction_response`

### Dependencies
- **LLM Providers**: OpenAI, Anthropic, or custom endpoints
- **RapidFuzz**: Fuzzy string matching for address parsing
- **Redis**: Job data storage and caching
- **RabbitMQ**: Message queue for task processing
- **PyMuPDF**: PDF processing (if needed)

### With Other Services
- **Backend Pipeline**: Sends extraction requests and receives responses
- **Redis**: Stores job data and processing results
- **Preprocess Service**: Provides preprocessed documents for extraction
- **AI Agent**: Consumes extracted data for further analysis

## Security

### Best Practices
- **Input Validation**: All document paths and data validated
- **API Key Security**: LLM API keys stored in environment variables
- **Message Security**: Proper message format validation
- **Error Handling**: No sensitive data in logs
- **Configuration**: Environment variables for secrets

### Data Security
- **PII Protection**: Careful handling of personally identifiable information
- **Data Sanitization**: Input data validation and cleaning
- **Access Control**: Restricted access to sensitive document data

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify RabbitMQ and Redis connectivity
4. Check LLM API access and quotas
5. Verify message formats and job data
6. Contact the development team

## License

Internal use only - © 2026 V7 Hyper Scaling Services