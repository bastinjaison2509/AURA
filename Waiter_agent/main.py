
import os
import sys
import time
import requests # <--- REQUIRED for A2A
import json     # <--- REQUIRED for A2A
from dotenv import load_dotenv

# 1. DISABLE TELEMETRY (Fixes the SSL Error)
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from src.crew import RestaurantCrew
from tools.custom_tool import RestaurantTools

load_dotenv()

def type_print(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.01)
    print("")

# --- NEW: A2A PROTOCOL CLIENT FUNCTION ---
def send_to_kitchen_a2a(order_summary):
    kitchen_host = "http://localhost:8000"
    print(f"\n🔵 [A2A Protocol] Initiating Handshake with {kitchen_host}...")

    try:
        # STEP 1: DISCOVERY (GET Agent Card)
        discovery_url = f"{kitchen_host}/.well-known/agent.json"
        resp = requests.get(discovery_url)
        
        if resp.status_code != 200:
            return f"❌ Protocol Error: Kitchen Agent not found (Status {resp.status_code})"
            
        card = resp.json()
        target_endpoint = card['endpoints']['message']
        print(f"🟢 [A2A Protocol] Discovered Agent: '{card['name']}'")

        # STEP 2: FORMAT MESSAGE (A2A Schema)
        payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": str(order_summary)}]
            }
        }

        # STEP 3: TRANSMISSION (POST)
        print(f"🔵 [A2A Protocol] Sending Order Payload...")
        post_resp = requests.post(target_endpoint, json=payload)
        
        if post_resp.status_code == 200:
            # Parse A2A Reply
            reply_data = post_resp.json()
            reply_text = reply_data['message']['parts'][0]['text']
            return reply_text
        else:
            return f"❌ Kitchen Error: {post_resp.text}"

    except requests.exceptions.ConnectionError:
        return "❌ Connection Error: Is 'kitchen_server.py' running in a separate terminal?"
    except Exception as e:
        return f"❌ Unexpected Error: {e}"

def main():
    print("--------------------------------------------------")
    
    type_print("Aura: Hi, I am Aura! Do you want to see the menu? (yes/no)")
    user_resp = input("You: ").lower().strip()
    
    if user_resp in ['yes', 'y']:
        print(f"\nAura: {RestaurantTools.fetch_menu.func('show')}")
    
    type_print("\nAura: What would you like to order? (e.g., '1 Burger takeaway')")
    order_input = input("You: ")
    
    type_print("\nAura: Approximately when will you reach the restaurant?")
    arrival_input = input("You: ")
    
    print("\n...Aura is thinking (using Google Gemini)...\n")
    
    # Run CrewAI (The Waiter)
    my_crew = RestaurantCrew()
    try:
        # We pass both order and arrival time to the Crew
        waiter_result = my_crew.run(inputs={
            'user_order': order_input,
            'arrival_time': arrival_input
        })
        
        print("\n################################")
        print("## WAITER SUMMARY (CrewAI) ##")
        print("################################")
        print(waiter_result)
        
        # --- HANDOFF TO KITCHEN AGENT ---
        print("\n--------------------------------------------------")
        print(">>> TRANSMITTING TO KITCHEN (A2A PROTOCOL) >>>")
        print("--------------------------------------------------")
        
        kitchen_ticket = send_to_kitchen_a2a(waiter_result)
        
        print("\n################################")
        print("## FINAL KITCHEN TICKET ##")
        print("################################")
        print(kitchen_ticket)

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()