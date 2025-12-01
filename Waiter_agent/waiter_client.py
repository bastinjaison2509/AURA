import os
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
import requests
import json
from dotenv import load_dotenv

# CrewAI Imports
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# Load environment variables
load_dotenv()
# os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# --- 1. DEFINE THE A2A CLIENT TOOL ---
# This is the bridge that speaks the "Agent Protocol"
class A2AProtocolTools:
    
    @tool("Send Order via A2A")
    def send_order(order_text: str):
        """
        Transmits the order to the Kitchen Agent using the official A2A Protocol.
        1. Performs Discovery (GET /.well-known/agent.json).
        2. Formats the message into the A2A Schema.
        3. Sends the payload to the discovered endpoint.
        """
        # The known address of the Kitchen Server (could be an IP or domain)
        kitchen_host = "http://localhost:8000"
        
        print(f"\n🔵 [A2A Tool] Initiating Protocol Handshake with {kitchen_host}...")

        # STEP A: DISCOVERY (GET Agent Card)
        try:
            discovery_url = f"{kitchen_host}/.well-known/agent.json"
            response = requests.get(discovery_url)
            
            if response.status_code != 200:
                return f"Protocol Error: Could not discover agent. Status {response.status_code}"
                
            agent_card = response.json()
            target_endpoint = agent_card['endpoints']['message']
            agent_name = agent_card['name']
            
            print(f"🟢 [A2A Tool] Discovered Agent: '{agent_name}'")
            print(f"🟢 [A2A Tool] Target Endpoint: {target_endpoint}")
            
        except Exception as e:
            return f"Protocol Discovery Failed: {str(e)}"

        # STEP B: FORMAT MESSAGE (Standard A2A Schema)
        # We must wrap the simple text in the "Message" > "Parts" structure
        protocol_payload = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": order_text
                    }
                ]
            }
        }

        # STEP C: TRANSMISSION (POST Message)
        try:
            print(f"🔵 [A2A Tool] Sending Message Payload...")
            post_response = requests.post(target_endpoint, json=protocol_payload)
            
            if post_response.status_code == 200:
                # Parse the A2A Response
                data = post_response.json()
                reply_text = data['message']['parts'][0]['text']
                print(f"🟢 [A2A Tool] Received Response from Kitchen!")
                return f"Kitchen Protocol Reply: {reply_text}"
            else:
                return f"Protocol Transmission Error: {post_response.text}"
                
        except Exception as e:
            return f"Protocol Transmission Failed: {str(e)}"

# --- 2. DEFINE THE CREW ---
class WaiterCrew:
    
    def run(self):
        # Setup Google Gemini for CrewAI
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )

        # Create the Agent
        aura = Agent(
            role='Aura (A2A Client)',
            goal='Receive orders and transmit them using the A2A Protocol tool.',
            backstory=(
                "You are a smart waiter agent. You do not print the order yourself. "
                "Your ONLY job is to take the user's input and use your 'Send Order via A2A' tool "
                "to send it to the kitchen."
            ),
            tools=[A2AProtocolTools.send_order], # <--- Equipping the tool
            llm=llm,
            verbose=True
        )

        # Create the Task
        # We hardcode a sample order here for demonstration
        task = Task(
            description=(
                "The customer has ordered: '2 Spicy Chicken Burgers and a large Coke, strictly no pickles'. "
                "They will arrive in 15 minutes. "
                "Send this full detail to the Kitchen Agent using the A2A Protocol."
            ),
            expected_output="The final confirmation string received from the Kitchen Agent.",
            agent=aura
        )

        # Run the Crew
        crew = Crew(agents=[aura], tasks=[task], process=Process.sequential)
        result = crew.kickoff()
        
        print("\n\n################################")
        print("## FINAL PROTOCOL RESULT ##")
        print("################################")
        print(result)

if __name__ == "__main__":
    WaiterCrew().run()