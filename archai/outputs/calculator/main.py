#!/usr/bin/env python3
"""
Simple Calculator - Monolithic Python Application
A basic calculator with CLI interface supporting basic arithmetic operations.
"""

import sys
import re
from typing import Union, Optional


class Calculator:
    """Calculator service containing all business logic."""
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract second number from first."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide first number by second."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b
    
    def power(self, a: float, b: float) -> float:
        """Raise first number to the power of second."""
        return a ** b
    
    def evaluate_expression(self, expression: str) -> float:
        """Evaluate a mathematical expression safely."""
        # Remove spaces and validate expression
        expression = expression.replace(" ", "")
        
        # Only allow numbers, operators, and parentheses
        if not re.match(r'^[\d+\-*/().]+$', expression):
            raise ValueError("Invalid characters in expression")
        
        try:
            # Use eval safely for basic math expressions
            result = eval(expression)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")


class CalculatorController:
    """Controller handling user interface and input/output."""
    
    def __init__(self):
        self.calculator = Calculator()
        self.history = []
    
    def display_menu(self):
        """Display the calculator menu."""
        print("\n" + "="*50)
        print("          PYTHON CALCULATOR")
        print("="*50)
        print("1. Basic Operations (+, -, *, /, **)")
        print("2. Expression Evaluation")
        print("3. View History")
        print("4. Clear History")
        print("5. Exit")
        print("-"*50)
    
    def get_number_input(self, prompt: str) -> float:
        """Get and validate number input from user."""
        while True:
            try:
                value = input(prompt)
                return float(value)
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def handle_basic_operations(self):
        """Handle basic arithmetic operations."""
        print("\nBasic Operations:")
        print("+ : Addition")
        print("- : Subtraction")
        print("* : Multiplication")
        print("/ : Division")
        print("** : Power")
        
        try:
            num1 = self.get_number_input("\nEnter first number: ")
            operation = input("Enter operation (+, -, *, /, **): ").strip()
            num2 = self.get_number_input("Enter second number: ")
            
            operations = {
                '+': self.calculator.add,
                '-': self.calculator.subtract,
                '*': self.calculator.multiply,
                '/': self.calculator.divide,
                '**': self.calculator.power
            }
            
            if operation not in operations:
                print("❌ Invalid operation. Please use +, -, *, /, or **")
                return
            
            result = operations[operation](num1, num2)
            calculation = f"{num1} {operation} {num2} = {result}"
            
            print(f"\n✅ Result: {result}")
            self.history.append(calculation)
            
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def handle_expression_evaluation(self):
        """Handle mathematical expression evaluation."""
        print("\nExpression Evaluation:")
        print("Example: 2 + 3 * 4, (10 + 5) / 3, 2**3")
        
        try:
            expression = input("\nEnter mathematical expression: ").strip()
            if not expression:
                print("❌ Please enter a valid expression.")
                return
            
            result = self.calculator.evaluate_expression(expression)
            calculation = f"{expression} = {result}"
            
            print(f"\n✅ Result: {result}")
            self.history.append(calculation)
            
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def display_history(self):
        """Display calculation history."""
        if not self.history:
            print("\n📝 No calculations in history.")
            return
        
        print(f"\n📝 Calculation History ({len(self.history)} items):")
        print("-" * 40)
        for i, calc in enumerate(self.history, 1):
            print(f"{i}. {calc}")
    
    def clear_history(self):
        """Clear calculation history."""
        if self.history:
            self.history.clear()
            print("\n🗑️  History cleared successfully.")
        else:
            print("\n📝 History is already empty.")
    
    def run(self):
        """Main application loop."""
        print("🔢 Welcome to Python Calculator!")
        
        while True:
            try:
                self.display_menu()
                choice = input("Select an option (1-5): ").strip()
                
                if choice == '1':
                    self.handle_basic_operations()
                elif choice == '2':
                    self.handle_expression_evaluation()
                elif choice == '3':
                    self.display_history()
                elif choice == '4':
                    self.clear_history()
                elif choice == '5':
                    print("\n👋 Thank you for using Python Calculator!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-5.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Calculator interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                input("Press Enter to continue...")


def main():
    """Application entry point."""
    if len(sys.argv) > 1:
        # Command line mode for quick calculations
        expression = " ".join(sys.argv[1:])
        calculator = Calculator()
        try:
            result = calculator.evaluate_expression(expression)
            print(f"{expression} = {result}")
        except ValueError as e:
            print(f"Error: {e}")
        return
    
    # Interactive mode
    app = CalculatorController()
    app.run()


if __name__ == "__main__":
    main()