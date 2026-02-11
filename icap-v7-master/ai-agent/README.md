# AI Agent Service

A production-ready microservice that handles AI-powered validation, document classification, and data processing tasks for document analysis pipelines using RabbitMQ messaging and machine learning models.

## Overview

The AI agent service provides intelligent document processing capabilities:
- **AWB/HAWB Validation**: Validates airway bill dates and supplier information
- **Document Classification**: Classifies sub-document types (HBL/MBL)
- **Data Modification**: Intelligent data correction and modification
- **Exception Handling**: Processes and resolves data exceptions
- **LLM Integration**: Uses Ollama models for intelligent text processing

## Features

### ✈️ AWB/HAWB Date Validator
- Validates transportation dates on airway bills
- Checks if dates are within one month from current date
- Uses both extracted data and LLM-based text analysis
- Provides position information for date locations

### 🏢 Supplier Validator
- Validates AWB/HAWB numbers and supplier information
- Fuzzy matching for supplier name identification
- Cross-references with known supplier databases

### 📋 Document Classification
- Classifies sub-document types (House Bill of Lading vs Master Bill of Lading)
- Intelligent document type detection
- Supports multiple document formats

### 🛠️ Data Modification Agents
- Intelligent data correction and modification
- CDZ (Customs Data Zone) data processing
- Automated data quality improvements

### 🤖 LLM Integration
- Ollama model integration for text processing
- LangChain framework for structured outputs
- JSON-based result parsing with Pydantic models

## Architecture

### Project Structure
```
ai-agent/
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── awb_hawb_agents/                # Airway bill processing agents
│   ├── date_validator_agent.py     # Date validation with LLM
│   ├── hwb_number_supplier_validator_agent.py # Supplier validation
│   └── position_finder_date.py      # Date position finder
│
├── sub_doc_class_agents/           # Document classification agents
│   └── sub_doc_class_selector.py   # HBL/MBL classification
│
├── cdz_data_modification_agents/   # Data modification agents
│   └── cdz_data_modification_agent.py # Data correction
│
├── exceptions_agents/              # Exception handling agents
│   ├── add_position_to_kv_exception.py # Position-based exceptions
│   └── kv_exception.py             # Key-value exception handling
│
├── rabbitmq/                       # Message queue infrastructure
│   ├── consumer.py                # Message consumer (main worker)
│   ├── handler.py                 # Task implementations
│   └── __init__.py
│
├── utils/                          # Shared utilities
│   ├── xml_or_ra_json_to_text.py  # Document conversion utilities
│   ├── config.py                  # Configuration management
│   └── timeout_utils.py           # Timeout handling
│
└── websocket_client.py            # Real-time log broadcasting
```

### Components
- **Validation Agents**: AI-powered document validation
- **Classification Agents**: Intelligent document type detection
- **Modification Agents**: Data quality improvement
- **RabbitMQ Workers**: Asynchronous message processing
- **Utils**: Shared utilities and configuration
- **LLM Integration**: Ollama model for text processing

### Message Flow
1. Backend service publishes message to `to_ai_agent` queue
2. AI agent worker consumes message and routes to appropriate handler
3. Handler calls specialized agents for document processing
4. Agents use LLM models for intelligent analysis
5. Results are formatted and validated
6. Response message is published back to `to_pipeline` queue
7. Backend service consumes response and continues processing

## RabbitMQ Message Types

### AWB/HAWB Date Validation
Publish message to `to_ai_agent` queue with message type `awb_hawb_date_validator`:

```json
{
  "batch_id": "batch-123",
  "documents": [
    {
      "document_type": "HouseAirwayBill",
      "ra_json": {},
      "data_json": {}
    }
  ],
  "job_id": "aidb:job:abc123:batch001",
  "service_identifier": "ai-agent"
}
```

### Supplier Validation
Publish message with message type `awb_or_hawb_no_and_supplier_validator`:

```json
{
  "batch_id": "batch-123",
  "awb_hawb_number": "123-456789",
  "supplier_info": {},
  "job_id": "aidb:job:abc123:batch001",
  "service_identifier": "ai-agent"
}
```

### Document Classification
Publish message with message type `hbl_mbl`:

```json
{
  "batch_id": "batch-123",
  "document_content": {},
  "classification_type": "hbl_mbl",
  "job_id": "aidb:job:abc123:batch001",
  "service_identifier": "ai-agent"
}
```

### Data Modification
Publish message with message type `cdz_data_modification`:

```json
{
  "batch_id": "batch-123",
  "data_to_modify": {},
  "modification_type": "cdz_correction",
  "job_id": "aidb:job:abc123:batch001",
  "service_identifier": "ai-agent"
}
```

Response is published back to `to_pipeline` queue with message type `ai_agent_response`:

```json
{
  "status_code": 200,
  "batch_id": "batch-123",
  "job_id": "aidb:job:abc123:batch001",
  "validation_result": {},
  "service_identifier": "ai-agent"
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
QUEUE_TO_AI_AGENT=to_ai_agent
QUEUE_TO_PIPELINE=to_pipeline

# Ollama LLM Configuration
OLLAMA_MODEL=gemma3:27b
OLLAMA_API_URL=http://ollama:11434

# LLM & AI Services
GROQ_API_KEY=your-groq-api-key-here
GROQ_API_SECRET=your-groq-api-secret-here
LOCAL_LLM_SERVER_API=http://localhost:5001/llm_service
TEMPERATURE=0.1
MAX_COMPLETION_TOKENS=30000
TOP_P=0.2
REASONING_EFFORT=medium
VECTOR_DATA_BASE_API=http://localhost:8020/api/v1

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

# Start Ollama service
docker-compose up -d ollama

# Pull required model
ollama pull gemma3:27b

# Run worker
python rabbitmq/consumer.py
```

## Monitoring

### Health Checks
- Worker status: Check RabbitMQ management console (http://localhost:15672)
- Redis connection: Verify Redis health
- Ollama connectivity: Check LLM model availability

### Logging
- **Structured Logging**: All logs use Python's logging module
- **Log Levels**: DEBUG, INFO, WARNING, ERROR (configurable via `LOG_LEVEL`)
- **Application logs**: `docker logs ai-agent-worker`
- **Error tracking**: Structured error logging with exception tracebacks

### Performance Metrics
- Message processing time
- Queue depth monitoring
- Worker resource usage
- LLM inference times
- Redis connection health

## Performance

### Optimization
- **Model Caching**: Ollama models cached in memory
- **Batch Processing**: Efficient handling of multiple documents
- **Message Queuing**: Asynchronous processing with RabbitMQ
- **Connection Pooling**: Optimized LLM client connections
- **Smart Caching**: Cache validation results for repeated queries

### Scaling
- **Horizontal Scaling**: Multiple worker containers
- **Resource Management**: Configurable memory and CPU limits
- **Queue Management**: RabbitMQ message routing and priorities
- **Load Balancing**: RabbitMQ distributes messages automatically

## Troubleshooting

### Common Issues

#### Ollama Model Errors
```bash
# Check model availability
ollama list

# Pull required model
ollama pull gemma3:27b

# Test Ollama connectivity
curl http://localhost:11434/api/generate -d '{"model":"gemma3:27b","prompt":"test"}'
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
The AI agent service integrates with the main pipeline via RabbitMQ:
- **to_ai_agent**: Queue for incoming AI processing tasks
- **to_pipeline**: Queue for processing results and responses
- **Message Types**: `awb_hawb_date_validator`, `awb_or_hawb_no_and_supplier_validator`, `hbl_mbl`, `cdz_data_modification`
- **Response Types**: `ai_agent_response`

### Dependencies
- **Ollama**: Local LLM inference engine
- **LangChain**: LLM framework and utilities
- **RapidFuzz**: Fuzzy string matching
- **dateutil**: Date parsing and validation
- **Redis**: Job data storage and caching
- **RabbitMQ**: Message queue for task processing
- **WebSockets**: Real-time log broadcasting

### With Other Services
- **Backend Pipeline**: Sends validation requests and receives responses
- **Redis**: Stores job data and processing results
- **Auto-Extraction Service**: Provides extracted data for validation
- **Preprocess Service**: Provides preprocessed documents
- **Frontend**: Receives real-time updates via WebSocket

## Security

### Best Practices
- **Input Validation**: All document data validated before processing
- **Model Security**: Ollama models run in isolated containers
- **Message Security**: Proper message format validation
- **Error Handling**: No sensitive data in logs
- **Configuration**: Environment variables for secrets

### Data Security
- **PII Protection**: Careful handling of personally identifiable information
- **Data Sanitization**: Input data validation and cleaning
- **Access Control**: Restricted access to sensitive document data
- **Model Privacy**: Local LLM inference keeps data on-premises

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify RabbitMQ and Redis connectivity
4. Check Ollama model availability
5. Verify message formats and job data
6. Contact the development team

## License

Internal use only - © 2026 V7 Hyper Scaling Services
