"""
History repository for managing calculation history
"""
from typing import List, Optional
from shared.models import CalculationResult


class HistoryRepository:
    """Repository for managing calculation history"""
    
    def __init__(self):
        self._history: List[CalculationResult] = []
    
    def save_calculation(self, calculation: CalculationResult) -> None:
        """Save a calculation to history"""
        self._history.append(calculation)
    
    def get_history(self) -> List[CalculationResult]:
        """Get all calculation history"""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear all calculation history"""
        self._history.clear()
    
    def get_last_result(self) -> Optional[float]:
        """Get the last calculation result"""
        return self._history[-1].result if self._history else None