# Integration Engine

Third-party integration system for the Autonomous Company OS. This engine handles API integrations, webhooks, data synchronization, and external service connections.

## Features

- **API Integration Hub** - Central hub for all third-party API integrations
- **Webhook Management** - Receive and process webhooks from external services
- **Data Synchronization** - Sync data between engines and external services
- **Authentication Management** - OAuth, API keys, token management
- **Rate Limiting** - Respect external API rate limits
- **Error Handling** - Robust error handling and retry logic
- **Integration Templates** - Pre-built integration templates
- **Monitoring** - Integration health and performance monitoring

## Architecture

```
┌─────────────┐    APIs      ┌──────────────┐
│   External │ ────────────> │  Integration │
│  Services  │               │  Hub         │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   API        │ │ Webhook │ │   Data     │
            │   Manager    │ │ Handler │ │  Sync      │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Authentication Manager      │
                    │  (OAuth, API Keys, Tokens)       │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Rate       │ │ Error   │ │ Monitor   │
            │   Limiter    │ │ Handler │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for integration data)
- Redis (for caching and queues)
- External API credentials

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/integration-engine.git
cd integration-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8044
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f integration-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/integrations` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `ENCRYPTION_KEY` | - | Encryption key for credentials |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Integrations
- `POST /integrations/create` - Create integration
- `GET /integrations/{integration_id}` - Get integration details
- `GET /integrations` - List integrations
- `POST /integrations/{integration_id}/sync` - Trigger sync
- `DELETE /integrations/{integration_id}` - Delete integration

### Webhooks
- `POST /webhooks/{integration_id}` - Receive webhook
- `GET /webhooks/{webhook_id}` - Get webhook details
- `GET /webhooks` - List webhooks

### Data Sync
- `POST /sync/configure` - Configure data sync
- `GET /sync/{sync_id}/status` - Get sync status
- `POST /sync/{sync_id}/trigger` - Trigger manual sync

### Templates
- `GET /templates` - List integration templates
- `POST /templates/{template_id}/install` - Install template

## Usage Examples

### Create Integration

```python
import httpx

async def create_integration():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8044/integrations/create",
            json={
                "integration_type": "hubspot",
                "name": "HubSpot CRM",
                "credentials": {
                    "api_key": "your-api-key"
                },
                "config": {
                    "sync_contacts": True,
                    "sync_deals": True
                }
            }
        )
        return response.json()
```

### Trigger Sync

```python
async def trigger_sync():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8044/integrations/integration_123/sync"
        )
        return response.json()
```

## Supported Integrations

### CRM
- **HubSpot** - Full CRM integration
- **Salesforce** - Enterprise CRM integration
- **Pipedrive** - Sales-focused CRM integration

### Marketing
- **Mailchimp** - Email marketing
- **SendGrid** - Email delivery
- **ActiveCampaign** - Marketing automation

### Analytics
- **Google Analytics** - Web analytics
- **Mixpanel** - Product analytics
- **Amplitude** - User analytics

### Productivity
- **Slack** - Team communication
- **Notion** - Documentation
- **Airtable** - Database

## Integration Features

- **OAuth 2.0** - Secure OAuth flow
- **API Key Authentication** - Simple API key auth
- **Webhook Processing** - Real-time webhook handling
- **Data Synchronization** - Bidirectional data sync
- **Rate Limiting** - Respect API limits
- **Error Handling** - Automatic retry logic
- **Monitoring** - Integration health checks

## Integration with Other Engines

### All Engines
- Provides integration capabilities
- Syncs data with external services
- Receives webhooks from external services

### Global State Manager
- Stores integration state
- Tracks sync status
- Manages integration metadata

## Monitoring

### Metrics
- Integration health status
- Sync success rate
- API call volume
- Error rate
- Latency metrics

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
