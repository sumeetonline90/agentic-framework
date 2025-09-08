# Agentic Framework

A modular, extensible framework for building AI agents. This framework provides a foundation for creating various types of AI agents with shared functionality, common interfaces, and easy extensibility.

## 🏗️ Architecture

```
agentic-framework/
├── core/                    # Core framework components
│   ├── base_agent.py       # Base agent class
│   ├── agent_manager.py    # Agent orchestration and management
│   ├── message_bus.py      # Inter-agent communication
│   └── context_manager.py  # Shared context and state management
├── agents/                 # Individual agent implementations
│   ├── __init__.py
│   ├── email_agent.py     # Email handling agent
│   ├── calendar_agent.py  # Calendar management agent
│   ├── chat_agent.py      # Conversational agent
│   ├── task_agent.py      # Task automation agent
│   ├── data_agent.py      # Data analysis agent
│   ├── news_agent.py      # News aggregation agent
│   ├── translation_agent.py # Translation agent
│   └── weather_agent.py   # Weather information agent
├── config/               # Configuration management
│   ├── __init__.py
│   ├── settings.py       # Framework settings
│   └── agent_config.py   # Agent-specific configurations
├── examples/            # Example implementations
│   └── basic_example.py # Basic usage example
├── data/                # Data storage directory
├── logs/                # Log files directory
├── true_agentic_demo.py # Main demo showcasing agent-to-agent communication
├── main.py             # Application entry point
├── quick_start.py      # Quick start script
├── quick_test.py       # Quick test script
├── fix_agents.py       # Agent maintenance script
├── requirements.txt    # Dependencies
├── docker-compose.yml  # Docker configuration
├── Dockerfile          # Docker image definition
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🚀 Features

- **Modular Design**: Easy to add new agents without modifying existing code
- **Inter-Agent Communication**: Agents can communicate and collaborate via message bus
- **Shared Context**: Common state and data sharing between agents
- **Multiple Agent Types**: Email, Weather, Calendar, Chat, Task, Data, News, and Translation agents
- **True Agentic Behavior**: Agents work independently and communicate directly
- **Configuration Management**: Flexible configuration system with environment variables
- **Logging & Monitoring**: Comprehensive logging and monitoring
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Interactive Demo**: Working demo showcasing agent-to-agent communication

## 🛠️ Quick Start

### 1. Installation

```bash
git clone https://github.com/sumeetonline90/agentic-framework.git
cd agentic-framework
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
# Edit .env with your email credentials
```

### 3. Run the Demo

```bash
python true_agentic_demo.py
```

This will start an interactive demo where you can:
- Choose a city for weather data
- Enter multiple email recipients
- Watch agents communicate directly with each other
- Send weather reports via email automatically

### 4. Alternative: Quick Test

```bash
python quick_test.py
```

## 📝 Creating a New Agent

### 1. Create Agent Class

```python
# agents/my_agent.py
from core.base_agent import BaseAgent
from core.message_bus import Message

class MyAgent(BaseAgent):
    def __init__(self, agent_id: str, config: dict):
        super().__init__(agent_id, config)
        self.capabilities = ["process_data", "generate_reports"]
    
    async def process_message(self, message: Message) -> dict:
        """Process incoming messages"""
        if message.type == "process_data":
            return await self._process_data(message.data)
        elif message.type == "generate_report":
            return await self._generate_report(message.data)
        else:
            return {"error": "Unknown message type"}
    
    async def _process_data(self, data: dict) -> dict:
        # Your data processing logic here
        return {"status": "processed", "result": "data_processed"}
    
    async def _generate_report(self, data: dict) -> dict:
        # Your report generation logic here
        return {"status": "completed", "report": "report_data"}
```

### 2. Register the Agent

```python
# In your main.py or agent_manager.py
from agents.my_agent import MyAgent

agent_manager.register_agent(MyAgent("my_agent", config))
```

### 3. Configure the Agent

```python
# config/agent_config.py
MY_AGENT_CONFIG = {
    "enabled": True,
    "auto_start": True,
    "capabilities": ["process_data", "generate_reports"],
    "settings": {
        "api_key": "your_api_key",
        "endpoint": "https://api.example.com"
    }
}
```

## 🔧 API Usage

### Send Message to Agent

```bash
curl -X POST http://localhost:8000/api/agents/my_agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "process_data",
    "data": {"input": "sample_data"},
    "priority": "high"
  }'
```

### Get Agent Status

```bash
curl http://localhost:8000/api/agents/my_agent/status
```

### List All Agents

```bash
curl http://localhost:8000/api/agents
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_my_agent.py

# Run with coverage
python -m pytest --cov=core --cov=agents tests/
```

## 📊 Monitoring

The framework includes built-in monitoring capabilities:

- Agent health checks
- Performance metrics
- Error tracking
- Usage statistics
- Resource utilization

## 🔌 Plugins

Create custom plugins to extend functionality:

```python
# plugins/my_plugin.py
from core.plugin_base import PluginBase

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__("my_plugin")
    
    async def execute(self, context: dict) -> dict:
        # Plugin logic here
        return {"result": "plugin_executed"}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@agentic-framework.com





