# Test Automation Orchestrator - Usage Guide

## Overview

The Test Automation Orchestrator provides a comprehensive CLI interface for managing your test automation system. It includes workflow orchestration, job scheduling, real-time monitoring, and a web-based dashboard.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the project:
```bash
python orchestrator.py init
```

## Quick Start

### Start the System
```bash
# Start with web dashboard (default: http://localhost:8080)
python orchestrator.py start

# Start on custom host/port
python orchestrator.py start --host 0.0.0.0 --port 9000

# Start in background (requires process manager)
python orchestrator.py start --background
```

### Check System Status
```bash
python orchestrator.py status
```

### Stop the System
```bash
python orchestrator.py stop
```

## Workflow Management

### List Workflows
```bash
python orchestrator.py workflow list
```

### Create a Workflow
```bash
# Simple workflow
python orchestrator.py workflow create "My Test Workflow"

# Workflow with configuration file
python orchestrator.py workflow create "API Tests" --config workflows/api_tests.json
```

Example workflow configuration (`workflows/api_tests.json`):
```json
{
  "name": "API Test Suite",
  "description": "Comprehensive API testing workflow",
  "steps": [
    {
      "name": "setup",
      "agent": "test_runner",
      "action": "setup_environment",
      "parameters": {
        "environment": "staging"
      }
    },
    {
      "name": "run_tests",
      "agent": "test_runner", 
      "action": "run_tests",
      "parameters": {
        "test_suite": "api",
        "parallel": true,
        "timeout": 300
      }
    },
    {
      "name": "generate_report",
      "agent": "report_generator",
      "action": "generate_html_report",
      "parameters": {
        "template": "detailed"
      }
    }
  ]
}
```

### Execute a Workflow
```bash
# Execute workflow by ID
python orchestrator.py workflow execute wf_12345

# Execute with parameters
python orchestrator.py workflow execute wf_12345 --params '{"environment": "production"}'
```

## Job Scheduling

### List Scheduled Jobs
```bash
python orchestrator.py schedule list
```

### Create Scheduled Jobs
```bash
# Daily at 2 AM
python orchestrator.py schedule create "Daily API Tests" "0 2 * * *" wf_12345

# Every 15 minutes
python orchestrator.py schedule create "Health Check" "*/15 * * * *" wf_67890

# With parameters
python orchestrator.py schedule create "Nightly Tests" "0 0 * * *" wf_12345 --params '{"full_suite": true}'
```

### Cron Schedule Examples
- `0 2 * * *` - Daily at 2:00 AM
- `*/15 * * * *` - Every 15 minutes
- `0 9-17 * * 1-5` - Every hour from 9 AM to 5 PM, Monday to Friday
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 0 1 * *` - Monthly on the 1st at midnight

## Configuration Management

### Show Configuration
```bash
# Show current environment config
python orchestrator.py config show

# Show specific environment
python orchestrator.py config show --environment production
```

### Validate Configuration
```bash
python orchestrator.py config validate
```

## Environment Management

The orchestrator supports multiple environments:

- **development** - Local development with debug logging
- **testing** - Automated testing environment
- **staging** - Pre-production testing
- **production** - Live production environment

### Switch Environments
```bash
# Start in production mode
python orchestrator.py --environment production start

# Check production status
python orchestrator.py --environment production status
```

## Dashboard Features

The web dashboard provides:

### Agent Management
- View agent status and health
- Start/stop agents
- Monitor agent performance metrics
- View agent logs

### Workflow Orchestration
- Create and edit workflows visually
- Monitor workflow executions
- View execution history and results
- Debug failed workflows

### Job Scheduling
- Manage scheduled jobs
- View job execution history
- Monitor job performance
- Create cron-based schedules

### System Monitoring
- Real-time system metrics (CPU, memory, disk)
- Agent performance monitoring
- System health dashboard
- Alert management

### Reports and Analytics
- Test execution reports
- Performance trends
- Success/failure analytics
- Custom dashboards

## API Integration

The orchestrator exposes REST APIs for integration:

### Workflow APIs
```bash
# List workflows
curl http://localhost:8080/api/workflows

# Execute workflow
curl -X POST http://localhost:8080/api/workflows/{id}/execute \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"environment": "staging"}}'
```

### Scheduler APIs
```bash
# List jobs
curl http://localhost:8080/api/scheduler/jobs

# Create job
curl -X POST http://localhost:8080/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Tests",
    "schedule": "0 2 * * *",
    "workflow_id": "wf_12345"
  }'
```

## WebSocket Events

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};

// Subscribe to specific events
ws.send(JSON.stringify({
  type: 'subscribe',
  events: ['workflow_started', 'workflow_completed', 'agent_status_changed']
}));
```

## Monitoring and Alerting

### System Metrics
- CPU usage monitoring
- Memory usage tracking
- Disk space monitoring
- Network performance
- Process monitoring

### Agent Metrics
- Execution success rates
- Response times
- Error rates
- Resource usage
- Health scores

### Custom Alerts
Configure alerts in the dashboard or via configuration files:

```json
{
  "alerts": [
    {
      "name": "High CPU Usage",
      "condition": "system.cpu_percent > 80",
      "duration": "5m",
      "actions": ["email", "webhook"]
    },
    {
      "name": "Workflow Failure Rate",
      "condition": "workflow.failure_rate > 0.1",
      "duration": "10m", 
      "actions": ["slack", "email"]
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   python orchestrator.py start --port 8081
   ```

2. **Permission Errors**
   - Ensure proper file permissions for logs and data directories
   - Run with appropriate user privileges

3. **Database Connection Issues**
   - Check database configuration in environment settings
   - Verify database server is running

4. **Agent Communication Failures**
   - Check network connectivity
   - Verify agent configurations
   - Review agent logs

### Debug Mode
```bash
python orchestrator.py --verbose start
```

### Log Locations
- System logs: `logs/system.log`
- Agent logs: `logs/agents/`
- Workflow logs: `logs/workflows/`
- API logs: `logs/api.log`

## Advanced Usage

### Custom Agents
Create custom agents by extending the base agent class:

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def execute_action(self, action: str, parameters: dict):
        # Custom implementation
        pass
```

### Workflow Templates
Create reusable workflow templates:

```json
{
  "template": "api_test_suite",
  "parameters": {
    "environment": {"type": "string", "required": true},
    "test_tags": {"type": "array", "default": []}
  },
  "steps": [
    // Template steps with parameter substitution
  ]
}
```

### Integration Hooks
Set up webhooks for external system integration:

```bash
# Configure webhook triggers
python orchestrator.py trigger create webhook \
  --url "/hooks/github" \
  --workflow wf_12345 \
  --events "push,pull_request"
```

## Support

For issues and questions:
1. Check the logs for error details
2. Review configuration validation
3. Consult the API documentation
4. Check system resource usage
5. Verify network connectivity

## Next Steps

- Explore the web dashboard at http://localhost:8080
- Create your first workflow
- Set up scheduled jobs
- Configure monitoring alerts
- Integrate with your CI/CD pipeline