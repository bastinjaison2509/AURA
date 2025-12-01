
import uvicorn
import json
from fastapi import FastAPI, Request
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.layout import Layout
from rich.live import Live

# Import your agent
from qsr_agent.agent import process_order

app = FastAPI()
console = Console()

# --- AGENT CARD ---
AGENT_CARD = {
    "name": "Kitchen Order Agent",
    "description": "ADK-powered Kitchen System.",
    "endpoints": {"message": "http://localhost:8000/a2a/message"}
}

@app.get("/.well-known/agent.json")
async def get_agent_card():
    return AGENT_CARD

@app.post("/a2a/message")
async def handle_a2a_message(request: Request):
    # 1. VISUALIZE INCOMING
    payload = await request.json()
    incoming_msg = payload.get("message", {})
    parts = incoming_msg.get("parts", [])
    user_text = next((p["text"] for p in parts if "text" in p), "")

    console.print(Panel(f"[bold cyan]{user_text}[/]", title="📨 INCOMING ORDER (CrewAI)", border_style="cyan"))

    # 2. RUN AGENT
    try:
        # We await the async agent
        console.print("[yellow]... Agent is thinking (Sub-agents & Guardrails running) ...[/]")
        adk_result = await process_order(user_text)
    except Exception as e:
        console.print(f"[bold red]❌ Error running agent: {e}[/]")
        return {"error": str(e)}

    # 3. EXTRACT & VISUALIZE STATE
    final_text = "No output"
    full_state_dump = {}

    if isinstance(adk_result, dict):
        # Extract the specific output text
        state = adk_result.get("state", {})
        full_state_dump = state # We keep the whole state to show the "Brain"
        
        if "kitchen_agent_output" in state:
            final_text = str(state["kitchen_agent_output"])
        elif "turn_history" in adk_result:
            final_text = adk_result["turn_history"][-1].get("response", "")

    # 4. SHOW THE BRAIN (Internal State)
    # This shows what your Queue, Inventory, and Load Balancer actually did
    # We filter for relevant keys to keep it clean
    important_keys = ["order", "kitchen_agent_output", "guardrail_blocked_input"]
    filtered_state = {k: v for k, v in full_state_dump.items() if k in important_keys}
    
    console.print(Panel(JSON.from_data(filtered_state), title="🧠 AGENT INTERNAL STATE (The Brain)", border_style="magenta"))

    # 5. SHOW FINAL OUTPUT
    console.print(Panel(f"[bold green]{final_text}[/]", title="👨‍🍳 FINAL KITCHEN TICKET", border_style="green"))

    # 6. RETURN A2A
    return {
        "message": {
            "role": "model",
            "parts": [{"kind": "text", "text": str(final_text)}]
        }
    }

if __name__ == "__main__":
    console.print(Panel("[bold white]🚀 ADK KITCHEN SERVER ONLINE (A2A Mode)[/]", style="on blue"))
    uvicorn.run(app, host="0.0.0.0", port=8000)