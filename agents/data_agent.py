"""
Data Processing Agent

Handles data operations, analysis, and management.
"""

import asyncio
import logging
import json
import csv
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from core.base_agent import BaseAgent
from core.message_bus import Message
from config.agent_config import AgentType


class DataFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    SQLITE = "sqlite"
    TEXT = "text"


class DataOperation(Enum):
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    TRANSFORM = "transform"
    VALIDATE = "validate"


@dataclass
class DataSource:
    source_id: str
    name: str
    type: str
    location: str
    format: DataFormat
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQuery:
    query_id: str
    source_id: str
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    result: Optional[Any] = None


class DataAgent(BaseAgent):
    """
    Data Processing Agent for handling data operations and analysis.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.data_sources: Dict[str, DataSource] = {}
        self.queries: Dict[str, DataQuery] = {}
        self.cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the data agent and initialize data management."""
        if await super().start():
            self.logger.info("Data agent started successfully")
            # Initialize default data sources
            await self._initialize_default_sources()
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the data agent."""
        if await super().stop():
            self.logger.info("Data agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for data operations."""
        try:
            if message.content.get("action") == "read_data":
                return await self._handle_read_data(message)
            elif message.content.get("action") == "write_data":
                return await self._handle_write_data(message)
            elif message.content.get("action") == "analyze_data":
                return await self._handle_analyze_data(message)
            elif message.content.get("action") == "transform_data":
                return await self._handle_transform_data(message)
            elif message.content.get("action") == "query_data":
                return await self._handle_query_data(message)
            elif message.content.get("action") == "add_source":
                return await self._handle_add_source(message)
            elif message.content.get("action") == "validate_data":
                return await self._handle_validate_data(message)
            else:
                return await super().process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": str(e)},
                priority=message.priority
            )
    
    async def _handle_read_data(self, message: Message) -> Message:
        """Handle data reading request."""
        source_id = message.content.get("source_id")
        query_params = message.content.get("query_params", {})
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            data = await self._read_from_source(source_id, query_params)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_read",
                    "source_id": source_id,
                    "data": data,
                    "count": len(data) if isinstance(data, list) else 1
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error reading data: {str(e)}"}
            )
    
    async def _handle_write_data(self, message: Message) -> Message:
        """Handle data writing request."""
        source_id = message.content.get("source_id")
        data = message.content.get("data")
        operation = message.content.get("operation", "write")
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            result = await self._write_to_source(source_id, data, operation)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_written",
                    "source_id": source_id,
                    "operation": operation,
                    "result": result
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error writing data: {str(e)}"}
            )
    
    async def _handle_analyze_data(self, message: Message) -> Message:
        """Handle data analysis request."""
        source_id = message.content.get("source_id")
        analysis_type = message.content.get("analysis_type", "basic")
        parameters = message.content.get("parameters", {})
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            # Read data first
            data = await self._read_from_source(source_id, {})
            
            # Perform analysis
            analysis_result = await self._perform_analysis(data, analysis_type, parameters)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_analyzed",
                    "source_id": source_id,
                    "analysis_type": analysis_type,
                    "result": analysis_result
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error analyzing data: {str(e)}"}
            )
    
    async def _handle_transform_data(self, message: Message) -> Message:
        """Handle data transformation request."""
        source_id = message.content.get("source_id")
        transformation = message.content.get("transformation", {})
        target_format = message.content.get("target_format")
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            # Read data
            data = await self._read_from_source(source_id, {})
            
            # Transform data
            transformed_data = await self._transform_data(data, transformation, target_format)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_transformed",
                    "source_id": source_id,
                    "transformed_data": transformed_data,
                    "target_format": target_format
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error transforming data: {str(e)}"}
            )
    
    async def _handle_query_data(self, message: Message) -> Message:
        """Handle data query request."""
        source_id = message.content.get("source_id")
        query = message.content.get("query")
        parameters = message.content.get("parameters", {})
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            result = await self._execute_query(source_id, query, parameters)
            
            # Store query
            query_id = f"query_{len(self.queries) + 1}"
            data_query = DataQuery(
                query_id=query_id,
                source_id=source_id,
                query=query,
                parameters=parameters,
                result=result
            )
            self.queries[query_id] = data_query
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_queried",
                    "query_id": query_id,
                    "source_id": source_id,
                    "result": result
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error querying data: {str(e)}"}
            )
    
    async def _handle_add_source(self, message: Message) -> Message:
        """Handle data source addition request."""
        source_data = message.content.get("source_data", {})
        
        source = DataSource(
            source_id=source_data.get("source_id", f"source_{len(self.data_sources) + 1}"),
            name=source_data.get("name", "Untitled Source"),
            type=source_data.get("type", "file"),
            location=source_data.get("location", ""),
            format=DataFormat(source_data.get("format", "json")),
            metadata=source_data.get("metadata", {})
        )
        
        self.data_sources[source.source_id] = source
        self.logger.info(f"Added data source: {source.source_id} - {source.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "source_added",
                "source_id": source.source_id,
                "source": {
                    "source_id": source.source_id,
                    "name": source.name,
                    "type": source.type,
                    "location": source.location,
                    "format": source.format.value,
                    "created_at": source.created_at.isoformat(),
                    "metadata": source.metadata
                }
            }
        )
    
    async def _handle_validate_data(self, message: Message) -> Message:
        """Handle data validation request."""
        source_id = message.content.get("source_id")
        validation_rules = message.content.get("validation_rules", {})
        
        if source_id not in self.data_sources:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Data source {source_id} not found"}
            )
        
        try:
            # Read data
            data = await self._read_from_source(source_id, {})
            
            # Validate data
            validation_result = await self._validate_data(data, validation_rules)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "data_validated",
                    "source_id": source_id,
                    "is_valid": validation_result["is_valid"],
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error validating data: {str(e)}"}
            )
    
    async def _initialize_default_sources(self):
        """Initialize default data sources."""
        # Add a default JSON file source
        default_source = DataSource(
            source_id="default_json",
            name="Default JSON Source",
            type="file",
            location="data/default.json",
            format=DataFormat.JSON
        )
        self.data_sources["default_json"] = default_source
        
        # Create data directory if it doesn't exist
        Path("data").mkdir(exist_ok=True)
        
        # Create default JSON file if it doesn't exist
        default_file = Path("data/default.json")
        if not default_file.exists():
            with open(default_file, "w") as f:
                json.dump({"data": [], "metadata": {"created": datetime.now().isoformat()}}, f)
    
    async def _read_from_source(self, source_id: str, query_params: Dict[str, Any]) -> Any:
        """Read data from a source."""
        source = self.data_sources[source_id]
        
        if source.format == DataFormat.JSON:
            return await self._read_json_file(source.location, query_params)
        elif source.format == DataFormat.CSV:
            return await self._read_csv_file(source.location, query_params)
        elif source.format == DataFormat.SQLITE:
            return await self._read_sqlite_db(source.location, query_params)
        else:
            raise ValueError(f"Unsupported format: {source.format}")
    
    async def _write_to_source(self, source_id: str, data: Any, operation: str) -> Dict[str, Any]:
        """Write data to a source."""
        source = self.data_sources[source_id]
        
        if source.format == DataFormat.JSON:
            return await self._write_json_file(source.location, data, operation)
        elif source.format == DataFormat.CSV:
            return await self._write_csv_file(source.location, data, operation)
        elif source.format == DataFormat.SQLITE:
            return await self._write_sqlite_db(source.location, data, operation)
        else:
            raise ValueError(f"Unsupported format: {source.format}")
    
    async def _read_json_file(self, file_path: str, query_params: Dict[str, Any]) -> Any:
        """Read data from JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Apply filters if specified
            if "filter" in query_params:
                filter_key = query_params["filter"]["key"]
                filter_value = query_params["filter"]["value"]
                if isinstance(data, list):
                    data = [item for item in data if item.get(filter_key) == filter_value]
                elif isinstance(data, dict):
                    data = data.get(filter_key, data)
            
            return data
        except FileNotFoundError:
            return []
        except Exception as e:
            raise Exception(f"Error reading JSON file: {e}")
    
    async def _write_json_file(self, file_path: str, data: Any, operation: str) -> Dict[str, Any]:
        """Write data to JSON file."""
        try:
            if operation == "write":
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
            elif operation == "append":
                existing_data = await self._read_json_file(file_path, {})
                if isinstance(existing_data, list):
                    existing_data.extend(data if isinstance(data, list) else [data])
                else:
                    existing_data = [existing_data, data]
                with open(file_path, "w") as f:
                    json.dump(existing_data, f, indent=2)
            
            return {"success": True, "operation": operation}
        except Exception as e:
            raise Exception(f"Error writing JSON file: {e}")
    
    async def _read_csv_file(self, file_path: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read data from CSV file."""
        try:
            data = []
            with open(file_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        except FileNotFoundError:
            return []
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")
    
    async def _write_csv_file(self, file_path: str, data: Any, operation: str) -> Dict[str, Any]:
        """Write data to CSV file."""
        try:
            if not isinstance(data, list):
                data = [data]
            
            if operation == "write":
                if data and isinstance(data[0], dict):
                    fieldnames = data[0].keys()
                    with open(file_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
            
            return {"success": True, "operation": operation}
        except Exception as e:
            raise Exception(f"Error writing CSV file: {e}")
    
    async def _read_sqlite_db(self, db_path: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read data from SQLite database."""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            query = query_params.get("query", "SELECT * FROM data")
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            conn.close()
            
            return data
        except Exception as e:
            raise Exception(f"Error reading SQLite database: {e}")
    
    async def _write_sqlite_db(self, db_path: str, data: Any, operation: str) -> Dict[str, Any]:
        """Write data to SQLite database."""
        try:
            conn = sqlite3.connect(db_path)
            
            if operation == "write" and isinstance(data, dict) and "query" in data:
                conn.execute(data["query"])
                conn.commit()
            
            conn.close()
            return {"success": True, "operation": operation}
        except Exception as e:
            raise Exception(f"Error writing SQLite database: {e}")
    
    async def _perform_analysis(self, data: Any, analysis_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis."""
        if analysis_type == "basic":
            return await self._basic_analysis(data)
        elif analysis_type == "statistical":
            return await self._statistical_analysis(data, parameters)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    async def _basic_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform basic data analysis."""
        if isinstance(data, list):
            return {
                "count": len(data),
                "type": "list",
                "empty": len(data) == 0
            }
        elif isinstance(data, dict):
            return {
                "count": len(data),
                "type": "dict",
                "keys": list(data.keys()),
                "empty": len(data) == 0
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)
            }
    
    async def _statistical_analysis(self, data: Any, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis."""
        if not isinstance(data, list) or not data:
            return {"error": "Data must be a non-empty list for statistical analysis"}
        
        # Basic statistics
        numeric_values = []
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)
            elif isinstance(item, (int, float)):
                numeric_values.append(item)
        
        if numeric_values:
            return {
                "count": len(numeric_values),
                "sum": sum(numeric_values),
                "average": sum(numeric_values) / len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values)
            }
        else:
            return {"error": "No numeric values found for statistical analysis"}
    
    async def _transform_data(self, data: Any, transformation: Dict[str, Any], target_format: Optional[str]) -> Any:
        """Transform data according to specified rules."""
        transformed_data = data
        
        # Apply transformations
        if "filter" in transformation:
            filter_key = transformation["filter"]["key"]
            filter_value = transformation["filter"]["value"]
            if isinstance(transformed_data, list):
                transformed_data = [item for item in transformed_data if item.get(filter_key) == filter_value]
        
        if "sort" in transformation:
            sort_key = transformation["sort"]["key"]
            reverse = transformation["sort"].get("reverse", False)
            if isinstance(transformed_data, list):
                transformed_data.sort(key=lambda x: x.get(sort_key, ""), reverse=reverse)
        
        if "limit" in transformation:
            limit = transformation["limit"]
            if isinstance(transformed_data, list):
                transformed_data = transformed_data[:limit]
        
        # Convert format if specified
        if target_format:
            if target_format == "json":
                return json.dumps(transformed_data, indent=2)
            elif target_format == "csv":
                # Convert to CSV string
                if isinstance(transformed_data, list) and transformed_data:
                    import io
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=transformed_data[0].keys())
                    writer.writeheader()
                    writer.writerows(transformed_data)
                    return output.getvalue()
        
        return transformed_data
    
    async def _execute_query(self, source_id: str, query: str, parameters: Dict[str, Any]) -> Any:
        """Execute a query on a data source."""
        source = self.data_sources[source_id]
        
        if source.format == DataFormat.SQLITE:
            return await self._execute_sqlite_query(source.location, query, parameters)
        else:
            # For other formats, implement custom query logic
            data = await self._read_from_source(source_id, {})
            return await self._apply_custom_query(data, query, parameters)
    
    async def _execute_sqlite_query(self, db_path: str, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SQLite query."""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(query, parameters)
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            conn.close()
            
            return data
        except Exception as e:
            raise Exception(f"Error executing SQLite query: {e}")
    
    async def _apply_custom_query(self, data: Any, query: str, parameters: Dict[str, Any]) -> Any:
        """Apply custom query logic to data."""
        # Simple query implementation for non-SQLite data
        if query == "count":
            return len(data) if isinstance(data, list) else 1
        elif query == "first":
            return data[0] if isinstance(data, list) and data else None
        elif query == "last":
            return data[-1] if isinstance(data, list) and data else None
        else:
            return data
    
    async def _validate_data(self, data: Any, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data according to rules."""
        errors = []
        warnings = []
        
        # Check required fields
        if "required_fields" in validation_rules:
            required_fields = validation_rules["required_fields"]
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for field in required_fields:
                            if field not in item:
                                errors.append(f"Missing required field '{field}' in item {i}")
            elif isinstance(data, dict):
                for field in required_fields:
                    if field not in data:
                        errors.append(f"Missing required field '{field}'")
        
        # Check data types
        if "field_types" in validation_rules:
            field_types = validation_rules["field_types"]
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for field, expected_type in field_types.items():
                            if field in item:
                                actual_type = type(item[field]).__name__
                                if actual_type != expected_type:
                                    warnings.append(f"Field '{field}' in item {i} has type {actual_type}, expected {expected_type}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for data agent."""
        try:
            action = message.content.get("action")
            
            if action == "read_data":
                return await self._handle_read_data(message)
            elif action == "write_data":
                return await self._handle_write_data(message)
            elif action == "analyze_data":
                return await self._handle_analyze_data(message)
            elif action == "transform_data":
                return await self._handle_transform_data(message)
            elif action == "query_data":
                return await self._handle_query_data(message)
            elif action == "add_data_source":
                return await self._handle_add_data_source(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get data agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_sources": len(self.data_sources),
            "total_queries": len(self.queries),
            "cache_size": len(self.cache),
            "sources_by_format": {
                format.value: len([s for s in self.data_sources.values() if s.format == format])
                for format in DataFormat
            }
        })
        return metrics
