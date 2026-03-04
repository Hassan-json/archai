#!/usr/bin/env python3
"""
Simple Calculator - Monolithic Architecture
A complete calculator application with layered architecture:
- Presentation Layer: CLI interface
- Business Layer: Calculator service with operations
- Data Layer: History repository for storing calculations
"""

import re
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass


# Data Models
@dataclass
class CalculationResult:
    """Model for calculation results"""
    expression: str
    result: float
    timestamp: datetime
    
    def __str__(self) -> str:
        return f"{self.expression} = {self.result} [{self.timestamp.strftime('%H:%M:%S')}]"


# Repository Layer - Data Access
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


# Service Layer - Business Logic
class CalculatorService:
    """Service containing calculator business logic"""
    
    def __init__(self, history_repo: HistoryRepository):
        self._history_repo = history_repo
        self._operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y,
            '**': lambda x, y: x ** y,
            '%': lambda x, y: x % y
        }
    
    def calculate(self, expression: str) -> CalculationResult:
        """
        Calculate mathematical expression and save to history
        Supports: +, -, *, /, ^, **, %, parentheses
        """
        try:
            # Clean and validate expression
            cleaned_expr = self._clean_expression(expression)
            
            # Handle special cases
            if cleaned_expr.lower() == 'ans':
                last_result = self._history_repo.get_last_result()
                if last_result is None:
                    raise ValueError("No previous calculation available")
                return CalculationResult("ans", last_result, datetime.now())
            
            # Replace ^ with ** for Python power operator
            cleaned_expr = cleaned_expr.replace('^', '**')
            
            # Validate expression contains only allowed characters
            if not re.match(r'^[0-9+\-*/().^%\s]+$', cleaned_expr.replace('**', '^')):
                raise ValueError("Invalid characters in expression")
            
            # Evaluate expression safely
            result = eval(cleaned_expr)
            
            if not isinstance(result, (int, float)):
                raise ValueError("Invalid calculation result")
            
            # Create calculation result
            calc_result = CalculationResult(expression, float(result), datetime.now())
            
            # Save to history
            self._history_repo.save_calculation(calc_result)
            
            return calc_result
            
        except ZeroDivisionError:
            raise ValueError("Division by zero is not allowed")
        except (SyntaxError, ValueError) as e:
            if "Invalid characters" in str(e) or "No previous calculation" in str(e):
                raise e
            raise ValueError(f"Invalid expression: {expression}")
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize the expression"""
        # Remove whitespace
        cleaned = expression.replace(' ', '')
        
        # Handle empty expression
        if not cleaned:
            raise ValueError("Empty expression")
        
        return cleaned
    
    def get_calculation_history(self) -> List[CalculationResult]:
        """Get all calculation history"""
        return self._history_repo.get_history()
    
    def clear_history(self) -> None:
        """Clear calculation history"""
        self._history_repo.clear_history()


# Controller Layer - Presentation/CLI Interface
class CalculatorController:
    """Controller handling user interface and input/output"""
    
    def __init__(self, calculator_service: CalculatorService):
        self._calculator_service = calculator_service
    
    def run(self) -> None:
        """Main application loop"""
        self._show_welcome()
        
        while True:
            try:
                user_input = input("\nCalc> ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if self._handle_command(user_input):
                    continue
                
                # Perform calculation
                result = self._calculator_service.calculate(user_input)
                print(f"Result: {result.result}")
                
            except KeyboardInterrupt:
                self._handle_exit()
                break
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
    
    def _handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True if command was processed."""
        command_lower = command.lower()
        
        if command_lower in ['exit', 'quit', 'q']:
            self._handle_exit()
            return True
        elif command_lower in ['help', 'h']:
            self._show_help()
            return True
        elif command_lower in ['history', 'hist']:
            self._show_history()
            return True
        elif command_lower in ['clear', 'cls']:
            self._clear_history()
            return True
        
        return False
    
    def _show_welcome(self) -> None:
        """Display welcome message"""
        print("=" * 50)
        print("  📧 Python Calculator - Monolithic Architecture")
        print("=" * 50)
        print("Type 'help' for commands, 'exit' to quit")
    
    def _show_help(self) -> None:
        """Display help information"""
        print("\n📋 Calculator Help:")
        print("  Operators: +, -, *, /, ^(or **), %")
        print("  Parentheses: ( ) for grouping")
        print("  Special: 'ans' for last result")
        print("  Commands:")
        print("    help, h     - Show this help")
        print("    history     - Show calculation history")
        print("    clear       - Clear history")
        print("    exit, quit  - Exit calculator")
        print("\n  Examples:")
        print("    2 + 3 * 4")
        print("    (10 + 5) / 3")
        print("    2 ^ 8")
        print("    ans + 5")
    
    def _show_history(self) -> None:
        """Display calculation history"""
        history = self._calculator_service.get_calculation_history()
        
        if not history:
            print("📝 No calculation history available")
            return
        
        print(f"\n📝 Calculation History ({len(history)} items):")
        for calc in history[-10:]:  # Show last 10 calculations
            print(f"  {calc}")
    
    def _clear_history(self) -> None:
        """Clear calculation history"""
        self._calculator_service.clear_history()
        print("🗑️ History cleared")
    
    def _handle_exit(self) -> None:
        """Handle application exit"""
        print("\n👋 Thanks for using the calculator!")


# Application Configuration and Bootstrap
class CalculatorApp:
    """Main application class - dependency injection and setup"""
    
    def __init__(self):
        # Initialize layers (dependency injection)
        self._history_repo = HistoryRepository()
        self._calculator_service = CalculatorService(self._history_repo)
        self._controller = CalculatorController(self._calculator_service)
    
    def start(self) -> None:
        """Start the calculator application"""
        self._controller.run()


# Application Entry Point
def main():
    """Application entry point"""
    app = CalculatorApp()
    app.start()


if __name__ == "__main__":
    main()