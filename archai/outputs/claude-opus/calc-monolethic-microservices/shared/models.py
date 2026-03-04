"""
Shared data models for calculator microservices
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class CalculationResult:
    """Model for calculation results"""
    expression: str
    result: float
    timestamp: datetime
    
    def __str__(self) -> str:
        return f"{self.expression} = {self.result} [{self.timestamp.strftime('%H:%M:%S')}]"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expression': self.expression,
            'result': self.result,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationResult':
        return cls(
            expression=data['expression'],
            result=data['result'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class CalculationRequest:
    """Model for calculation requests"""
    expression: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {'expression': self.expression}


@dataclass
class ServiceResponse:
    """Standard response model for all services"""
    success: bool
    data: Any = None
    error: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }