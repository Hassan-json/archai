#!/usr/bin/env python3
"""
Calculator CLI Client - Microservices Version
Command-line interface that communicates with calculator microservices via API Gateway
"""
import requests
import os
import sys
from typing import Optional, List
import json
from datetime import datetime

class CalculatorClient:
    """CLI client for calculator microservices"""
    
    def __init__(self, gateway_url: str = None):
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL", "http://localhost:8000")
        self.session = requests.Session()
        self.session.timeout = 10
    
    def calculate(self, expression: str) -> Optional[dict]:
        """Send calculation request to API Gateway"""
        try:
            response = self.session.post(
                f"{self.gateway_url}/api/calculate",
                json={'expression': expression}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            print(f"Connection error: {str(e)}")
            return None
    
    def get_history(self) -> Optional[List[dict]]:
        """Get calculation history from API Gateway"""
        try:
            response = self.session.get(f"{self.gateway_url}/api/history")
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            else:
                print(f"Error getting history: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            print(f"Connection error: {str(e)}")
            return None
    
    def clear_history(self) -> bool:
        """Clear calculation history via API Gateway"""
        try:
            response = self.session.delete(f"{self.gateway_url}/api/history")
            
            if response.status_code == 200:
                return True
            else:
                print(f"Error clearing history: {response.json().get('detail', 'Unknown error')}")
                return False
                
        except requests.RequestException as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def check_health(self) -> bool:
        """Check if services are healthy"""
        try:
            response = self.session.get(f"{self.gateway_url}/api/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"Gateway Status: {health_data.get('status', 'unknown')}")
                
                services = health_data.get('services', {})
                for service, status in services.items():
                    print(f"  {service.capitalize()}: {status}")
                
                return health_data.get('status') == 'healthy'
            else:
                print("Health check failed")
                return False
                
        except requests.RequestException as e:
            print(f"Connection error: {str(e)}")
            return False

class CalculatorCLI:
    """Command-line interface for the calculator"""
    
    def __init__(self):
        self.client = CalculatorClient()
        self.commands = {
            'help': self._show_help,
            'history': self._show_history,
            'clear': self._clear_history,
            'health': self._check_health,
            'exit': self._exit,
            'quit': self._exit
        }
    
    def run(self):
        """Run the CLI application"""
        self._show_welcome()
        
        while True:
            try:
                user_input = input("\nCalculator> ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in self.commands:
                    if self.commands[user_input.lower()]():
                        break
                    continue
                
                # Process calculation
                self._process_calculation(user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
    
    def _show_welcome(self):
        """Display welcome message"""
        print("=" * 60)
        print("    Calculator - Microservices Architecture")
        print("=" * 60)
        print("Available commands:")
        print("  help    - Show this help message")
        print("  history - Show calculation history")
        print("  clear   - Clear calculation history")
        print("  health  - Check service health")
        print("  exit    - Exit the calculator")
        print("\nSupported operations: +, -, *, /, ^, %, ()")
        print("Special: 'ans' for last result")
        print("=" * 60)
    
    def _process_calculation(self, expression: str):
        """Process a calculation expression"""
        result = self.client.calculate(expression)
        
        if result and result.get('success'):
            data = result.get('data', {})
            expr = data.get('expression', expression)
            value = data.get('result', 0)
            timestamp = data.get('timestamp', '')
            
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = ''
            else:
                time_str = ''
            
            print(f"\n{expr} = {value}" + (f" [{time_str}]" if time_str else ""))
    
    def _show_help(self) -> bool:
        """Show help message"""
        self._show_welcome()
        return False
    
    def _show_history(self) -> bool:
        """Show calculation history"""
        history = self.client.get_history()
        
        if history is None:
            return False
        
        if not history:
            print("\nNo calculations in history.")
            return False
        
        print("\n" + "=" * 50)
        print("CALCULATION HISTORY")
        print("=" * 50)
        
        for calc in history:
            expr = calc.get('expression', '')
            result = calc.get('result', 0)
            timestamp = calc.get('timestamp', '')
            
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = ''
            else:
                time_str = ''
            
            print(f"{expr} = {result}" + (f" [{time_str}]" if time_str else ""))
        
        print("=" * 50)
        return False
    
    def _clear_history(self) -> bool:
        """Clear calculation history"""
        if self.client.clear_history():
            print("\nHistory cleared successfully!")
        return False
    
    def _check_health(self) -> bool:
        """Check service health"""
        print("\nChecking service health...")
        self.client.check_health()
        return False
    
    def _exit(self) -> bool:
        """Exit the application"""
        print("\nGoodbye!")
        return True

def main():
    """Main entry point"""
    # Check if gateway URL is provided as command line argument
    gateway_url = None
    if len(sys.argv) > 1:
        gateway_url = sys.argv[1]
    
    # Initialize and run CLI
    cli = CalculatorCLI()
    if gateway_url:
        cli.client.gateway_url = gateway_url
    
    print(f"Connecting to gateway: {cli.client.gateway_url}")
    
    # Check initial connectivity
    if not cli.client.check_health():
        print("Warning: Services may not be available")
        print("Make sure all microservices are running")
    
    cli.run()

if __name__ == "__main__":
    main()