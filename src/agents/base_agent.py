"""
Base Agent Class

Provides common functionality and structure for all testing agents.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json
from datetime import datetime


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentConfig:
    """Configuration for agents"""
    name: str
    description: str = ""
    timeout: int = 300  # 5 minutes default
    retry_count: int = 3
    retry_delay: int = 5
    enabled: bool = True
    environment: str = "development"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result of agent execution"""
    agent_name: str
    status: AgentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all testing agents.
    
    Provides common functionality like logging, error handling, retries,
    and status management.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.logger = self._setup_logger()
        self.result: Optional[AgentResult] = None
        self._callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_complete': [],
            'on_error': [],
            'on_cancel': []
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the agent"""
        logger = logging.getLogger(f"agent.{self.config.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def add_callback(self, event: str, callback: Callable):
        """Add callback for agent events"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger callbacks for an event"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")
    
    async def execute(self, **kwargs) -> AgentResult:
        """
        Execute the agent with retry logic and error handling
        """
        if not self.config.enabled:
            self.logger.info(f"Agent {self.config.name} is disabled")
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.CANCELLED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0.0,
                error="Agent is disabled"
            )
        
        start_time = datetime.now()
        self.result = AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.RUNNING,
            start_time=start_time
        )
        
        self.status = AgentStatus.RUNNING
        self.logger.info(f"Starting agent {self.config.name}")
        self._trigger_callbacks('on_start')
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.retry_count:
            try:
                # Execute with timeout
                result_data = await asyncio.wait_for(
                    self._execute_impl(**kwargs),
                    timeout=self.config.timeout
                )
                
                # Success
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.result.status = AgentStatus.COMPLETED
                self.result.end_time = end_time
                self.result.duration = duration
                self.result.data = result_data or {}
                
                self.status = AgentStatus.COMPLETED
                self.logger.info(f"Agent {self.config.name} completed successfully in {duration:.2f}s")
                self._trigger_callbacks('on_complete', self.result)
                
                return self.result
                
            except asyncio.TimeoutError:
                last_error = f"Agent timed out after {self.config.timeout} seconds"
                self.logger.warning(f"Attempt {retry_count + 1} timed out: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {retry_count + 1} failed: {last_error}")
            
            retry_count += 1
            if retry_count <= self.config.retry_count:
                self.logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                await asyncio.sleep(self.config.retry_delay)
        
        # All retries failed
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.result.status = AgentStatus.FAILED
        self.result.end_time = end_time
        self.result.duration = duration
        self.result.error = last_error
        
        self.status = AgentStatus.FAILED
        self.logger.error(f"Agent {self.config.name} failed after {retry_count} attempts: {last_error}")
        self._trigger_callbacks('on_error', self.result)
        
        return self.result
    
    async def cancel(self):
        """Cancel the agent execution"""
        self.status = AgentStatus.CANCELLED
        self.logger.info(f"Agent {self.config.name} cancelled")
        self._trigger_callbacks('on_cancel')
    
    @abstractmethod
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """
        Implementation of the agent's main logic.
        Must be implemented by subclasses.
        
        Returns:
            Dict containing the result data
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        return self.status
    
    def get_result(self) -> Optional[AgentResult]:
        """Get the last execution result"""
        return self.result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            'name': self.config.name,
            'description': self.config.description,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'environment': self.config.environment,
            'metadata': self.config.metadata,
            'result': {
                'status': self.result.status.value if self.result else None,
                'duration': self.result.duration if self.result else None,
                'error': self.result.error if self.result else None,
                'start_time': self.result.start_time.isoformat() if self.result else None,
                'end_time': self.result.end_time.isoformat() if self.result and self.result.end_time else None
            } if self.result else None
        }
    
    def __str__(self) -> str:
        return f"Agent({self.config.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()