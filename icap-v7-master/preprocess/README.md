# Preprocess Service

A production-ready microservice that handles PDF and image preprocess tasks for document analysis pipelines using RabbitMQ messaging.

## Overview

The preprocess service provides three main functionalities:
- **Dense Page Detection**: Identifies pages with high text density using ML models
- **Electronic PDF Detection**: Determines if PDFs are electronic or scanned
- **Electronic PDF Processing**: Processes PDF files and converts them to RAJson format

## Features

### 📄 Dense Page Detection
- Uses ONNX MobileNetV3 model for text detection
- Identifies pages that may need special processing
- Supports batch processing of multiple image directories

### 🔍 Electronic PDF Detection  
- Analyzes PDF structure to determine if electronic or scanned
- Uses PyMuPDF and pdf2image for analysis
- Fast processing for large document batches

### 🔄 Electronic PDF Processing
- Converts PDFs to RAJson format
- Supports batch processing with metadata
- Handles various PDF types and qualities

## Architecture

### Project Structure
```
preprocess/
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── ARCHITECTURE.md                 # Detailed architecture documentation
│
├── services/                       # Business logic layer
│   ├── detect_pdf.py              # PDF detection service
│   ├── electronic_pdf.py          # PDF processing service
│   └── dense_page_detector/       # ML-based dense page detection
│
├── rabbitmq/                       # Message queue infrastructure
│   ├── consumer.py                # Message consumer (main worker)
│   ├── handler.py                 # Task implementations
│   └── producer.py                # Message publisher
│
├── utils/                          # Shared utilities
│   ├── config.py                  # Configuration management
│   ├── redis.py                   # Redis operations
│   └── timeout_utils.py           # Timeout handling
│
└── model/                          # ML models
    └── onnxtr/                    # ONNX model files
```

### Components
- **Services Layer**: Core business logic for PDF processing
- **RabbitMQ Workers**: Asynchronous message processing
- **Utils**: Shared utilities and configuration
- **ML Models**: ONNX models for dense page detection

### Message Flow
1. Backend service publishes message to `to_preprocess` queue
2. Preprocess worker consumes message and routes to appropriate handler
3. Handler calls service layer to perform actual processing
4. Results are stored in Redis (for electronic PDF processing)
5. Response message is published back to `to_pipeline` queue
6. Backend service consumes response and continues processing

## RabbitMQ Message Types

### Dense Page Detection
Publish message to `to_preprocess` queue with message type `ignore_dense_pages`:

```json
{
  "image_dir_paths": ["/path/to/images"],
  "job_id": "aidb:job:abc123:batch001",
  "batch_id": "batch-123",
  "attachments_folder": "/path/to/attachments",
  "train_batch_log": false,
  "service_identifier": "preprocess"
}
```

Response is published back to `to_pipeline` queue with message type `ignore_dense_pages_response`:

```json
{
  "status_code": 200,
  "job_id": "aidb:job:abc123:batch001",
  "attachments_folder": "/path/to/attachments",
  "batch_id": "batch-123",
  "train_batch_log": false,
  "service_identifier": "preprocess",
  "dense_pages_list": []
}
```

### Electronic PDF Detection
Publish message to `to_preprocess` queue with message type `categorize_pdfs`:

```json
{
  "pdf_paths": ["/path/to/document.pdf"],
  "job_id": "aidb:job:abc123:batch001",
  "service_identifier": "preprocess"
}
```

Response is published back to `to_pipeline` queue with message type `pdf_categorization_response`:

```json
{
  "status_code": 200,
  "job_id": "aidb:job:abc123:batch001",
  "pdf_paths": ["/path/to/document.pdf"],
  "electronic_pdfs": [],
  "scanned_pdfs": []
}
```

### Electronic PDF Processing
Publish message to `to_preprocess` queue with message type `process_files`:

```json
{
  "job_id": "aidb:job:abc123:batch001",
  "parent_batch_id": "TN20260115.00018",
  "batch_upload_mode": "training"
}
```

Response is published back to `to_pipeline` queue with message type `electronic_pdf_response`:

```json
{
  "status_code": 200,
  "job_id": "aidb:job:abc123:batch001",
  "parent_batch_id": "TN20260115.00018",
  "batch_upload_mode": "training"
}
```

**Note**: For electronic PDF processing, the actual file paths and processing parameters are retrieved from Redis using the `job_id`. The job information must be stored in Redis before publishing the message.

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
QUEUE_TO_PREPROCESS=to_preprocess
QUEUE_TO_PIPELINE=to_pipeline

# Worker Configuration  
WORKER_TIMEOUT=30

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
- Model loading: Check startup logs

### Logging
- **Structured Logging**: All logs use Python's logging module
- **Log Levels**: DEBUG, INFO, WARNING, ERROR (configurable via `LOG_LEVEL`)
- **Application logs**: `docker logs preprocess-worker`
- **Error tracking**: Structured error logging with exception tracebacks

### Performance Metrics
- Message processing time
- Queue depth monitoring
- Worker resource usage
- Redis connection health

## Performance

### Optimization
- **Model Caching**: ONNX models cached in memory
- **Batch Processing**: Efficient handling of multiple files
- **Message Queuing**: Asynchronous processing with RabbitMQ
- **Direct Imports**: No unnecessary abstraction layers

### Scaling
- **Horizontal Scaling**: Multiple worker containers
- **Resource Management**: Configurable memory limits
- **Queue Management**: RabbitMQ message routing and priorities
- **Load Balancing**: RabbitMQ distributes messages automatically

## Troubleshooting

### Common Issues

#### Model Loading Errors
```bash
# Check model file exists
ls -la /app/model/onnxtr/

# Verify permissions
chmod +r /app/model/onnxtr/*.onnx
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
The preprocess service integrates with the main pipeline via RabbitMQ:
- **to_preprocess**: Queue for incoming processing tasks
- **to_pipeline**: Queue for processing results and responses
- **Message Types**: `ignore_dense_pages`, `categorize_pdfs`, `process_files`
- **Response Types**: `ignore_dense_pages_response`, `pdf_categorization_response`, `electronic_pdf_response`

### Dependencies
- **ONNX Runtime**: ML model inference
- **PyMuPDF**: PDF analysis
- **pdf2image**: PDF to image conversion
- **OpenCV**: Image processing
- **Redis**: Job data storage and caching
- **RabbitMQ**: Message queue for task processing

### With Other Services
- **Backend Pipeline**: Sends processing requests and receives responses
- **Redis**: Stores job data and processing results
- **AI Agent**: Provides processed documents for analysis

## Security

### Best Practices
- **Input Validation**: All file paths validated
- **Resource Limits**: Configurable processing timeouts
- **Message Security**: Proper message format validation
- **Error Handling**: No sensitive data in logs
- **Configuration**: Environment variables for secrets

### File Security
- **Path Traversal**: Prevents directory escape attacks
- **File Type Validation**: Only allowed formats processed
- **Size Limits**: Configurable maximum file sizes

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify RabbitMQ and Redis connectivity
4. Check message formats and job data in Redis
5. Contact the development team

## License

Internal use only - © 2026 V7 Hyper Scaling Services