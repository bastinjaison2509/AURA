import json
import os
from crewai.tools import tool

class RestaurantTools:
    
    @tool("Fetch Menu from File")
    def fetch_menu(query: str = "menu"):
        """
        Reads the menu items and prices from the local Data/menu.json file.
        Useful for getting prices and available items.
        """
        # Finds Data/menu.json relative to the current working directory
        file_path = os.path.join(os.getcwd(), 'Data', 'menu.json')
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return str(data)
        except FileNotFoundError:
            return f"Error: Could not find menu.json at {file_path}. Please check the file structure."

    @tool("Estimate Preparation Time")
    def estimate_time(order_text: str):
        """
        Calculates estimated time based on item complexity.
        Input should be the list of items (e.g., '1 burger, 2 cokes').
        """
        base_time = 10
        extra_time = 0
        text = order_text.lower()
        
        if "pizza" in text or "chicken" in text:
            extra_time += 15
        if "burger" in text:
            extra_time += 10
        if "soup" in text or "salad" in text:
            extra_time += 5
            
        return f"{base_time + extra_time} minutes"