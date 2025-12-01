# Aura – Autonomous Multi-Agent QSR Operating System
 
**Aura** is a multi-agent system designed to automate the full workflow of a Quick Service Restaurant (QSR). By leveraging **CrewAI**, **Google Agent Development Kit (ADK)**, and the **A2A (Agent-to-Agent) protocol**, Aura seamlessly connects customer-facing agents with kitchen orchestration agents to manage end-to-end restaurant operations.
 
---
 
## 🔹 What This Project Does
 
Aura acts as the central nervous system for a restaurant, handling everything from the initial customer greeting to the final quality check of the food.
 
* **Conversational Ordering:** Uses CrewAI + Gemini to handle natural language customer interactions.
* **Structured Data Conversion:** Converts ambiguous spoken orders into structured JSON data.
* **Kitchen Orchestration:** Sends orders via A2A to the Back-of-House (BOH) agents.
* **Automated Workflow (ADK):**
    * Validates orders and assigns queue priority.
    * Breaks down orders into specific cooking tasks.
    * Performs assembly quality checks using AI.
    * Plans delivery logistics.
* **Parallel Enrichment:** Simultaneously handles forecasting, inventory updates, loyalty points, and sentiment analysis.
* **Final Output:** Produces a refined, operational JSON object ready for downstream systems.
 
---
 
## 🔹 Key Features
 
* **Unified Multi-Agent System:** Seamless integration of Front-of-House (FOH) and Back-of-House (BOH) operations.
* **Hybrid Workflows:** Supports both sequential (step-by-step cooking) and parallel (enrichment) agent workflows.
* **Tool Usage:**
    * *Custom Tools:* Menu retrieval, prep time estimation.
    * *Built-in Tools:* Google Search, code execution.
* **Long-Running Agents:** AI capabilities for sustained tasks like visual assembly checking.
* **State Management:** Robust session handling across agent interactions.
* **A2A Protocol:** Demonstrates cross-framework communication between CrewAI and Google ADK.
 
 
 
## 🔹 Architecture
 
The system is divided into two distinct but interconnected layers:
 
### 1. Front-of-House (CrewAI)
* **Role:** Customer Interface.
* **Responsibilities:**
    * Displays the menu.
    * Understands and processes user intent.
    * Estimates pricing and preparation time.
    * Transmits structured order data via A2A.
 
### 2. Back-of-House (Google ADK)
* **Role:** Operational Orchestration.
* **Agents:**
    * **Order Loader:** Standardizes incoming data.
    * **Queue Manager:** Prioritizes orders.
    * **Kitchen Load Balancer:** Assigns tasks to stations.
    * **AI Assembly Checker:** Visually verifies food quality.
    * **Notifier:** Alerts staff to anomalies.
    * **Enrichment Agents:** Forecasting, Inventory, and Loyalty management.
 
---
 
## 🔹 Tech Stack
 
* **Language:** Python
* **LLM:** Gemini Flash
* **Frameworks:** CrewAI, Google ADK (Agent Development Kit)
* **Protocol:** A2A (Agent-to-Agent)
* **API:** FastAPI
 
---
 
## 🔹 Getting Started
 
### Prerequisites
* Python 3.10 or higher
* Gemini API Key
 
### Installation
 
1.  Clone the repository:
    ```bash
    git clone https://github.com/bastinjaison2509/AURA
    cd aura
    ```
 
2.  Install dependencies:
    ```bash
    cd kitchen_server
    pip install -r requirements.txt
 
    cd /waiter
    pip install -r requirements.txt
 
    ```
 
### Usage
 
The system requires two separate processes to run—the Kitchen Server (ADK) and the Client Agent in different terminal(CrewAI).
 
**1. Start the ADK Kitchen Server:**
```bash
python adk/kitcher_server.py
 
2. Start the CrewAI Client Agent:
 
Bash
 
python crew/main.py
🔹 Project Purpose
This project was designed for the Kaggle Agents Intensive Capstone (Enterprise Agents Track). It demonstrates advanced agentic engineering concepts, including:
 
Complex multi-agent reasoning.
 
Implementation of the A2A protocol.
 
Tool-augmented agent capabilities.
 
Orchestration across multiple frameworks.
 
🔹 Future Enhancements
[ ] Visual Intelligence: Real-time CCTV integration for assembly inspection.
 
[ ] Deployment: Containerization and deployment to Google Cloud Run.
 
[ ] Scaling: Multi-outlet orchestration logic.
 
[ ] Voice: Direct voice-based ordering integration.
 