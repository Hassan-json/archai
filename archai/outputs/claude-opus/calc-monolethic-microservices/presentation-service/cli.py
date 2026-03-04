"""
CLI interface for calculator microservices
"""
import requests
from typing import Optional


class CalculatorCLI:
    """Command Line Interface for the calculator"""
    
    def __init__(self, api_gateway_url: str = "http://api-gateway:5000"):
        self.api_gateway_url = api_gateway_url
    
    def run(self) -> None:
        """Run the CLI interface"""
        print("=== Calculator Microservices CLI ===")
        print("Enter mathematical expressions or commands:")
        print("Commands: 'history', 'clear', 'help', 'quit'")
        print("Use 'ans' to reference the last result")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.lower() == 'history':
                    self._show_history()
                elif user_input.lower() == 'clear':
                    self._clear_history()
                else:
                    self._calculate(user_input)
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _calculate(self, expression: str) -> None:
        """Send calculation request to API gateway"""
        try:
            response = requests.post(
                f"{self.api_gateway_url}/calculate",
                json={"expression": expression}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"{expression} = {data['result']}")
                else:
                    print(f"Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"Service error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
    
    def _show_history(self) -> None:
        """Display calculation history"""
        try:
            response = requests.get(f"{self.api_gateway_url}/history")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    history = data.get('history', [])
                    if history:
                        print("\n=== Calculation History ===")
                        for calc in history:
                            timestamp = calc['timestamp']
                            print(f"{calc['expression']} = {calc['result']} [{timestamp}]")
                        print("-" * 30)
                    else:
                        print("No calculations in history")
                else:
                    print(f"Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"Service error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
    
    def _clear_history(self) -> None:
        """Clear calculation history"""
        try:
            response = requests.delete(f"{self.api_gateway_url}/history")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("History cleared")
                else:
                    print(f"Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"Service error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
    
    def _show_help(self) -> None:
        """Show help information"""
        help_text = """
=== Calculator Help ===
Supported operations:
  + : Addition (2 + 3)
  - : Subtraction (5 - 2)
  * : Multiplication (4 * 6)
  / : Division (10 / 2)
  ^ or ** : Power (2 ^ 3 or 2 ** 3)
  % : Modulo (10 % 3)
  () : Parentheses for grouping

Special keywords:
  ans : Use the result of the last calculation

Commands:
  history : Show calculation history
  clear   : Clear calculation history
  help    : Show this help
  quit    : Exit the calculator

Examples:
  > 2 + 3
  > 5 * (10 - 3)
  > 2 ^ 8
  > ans + 5
  > sqrt(16)  [Note: Use 16**0.5 for square root]
"""
        print(help_text)


if __name__ == "__main__":
    cli = CalculatorCLI()
    cli.run()