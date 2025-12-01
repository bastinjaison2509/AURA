
import os
from crewai import Agent, Crew, Process, Task, LLM
from tools.custom_tool import RestaurantTools

class RestaurantCrew:
    
    def __init__(self):
        # 1. Setup Google Gemini using the native CrewAI LLM class
        # We use the "gemini/" prefix so LiteLLM knows which provider to use.
        self.llm = LLM(
            model="gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5,
            verbose=True,
            max_iter=3,
        )
        
        self.tools = [RestaurantTools.fetch_menu, RestaurantTools.estimate_time]

    def aura_agent(self) -> Agent:
        return Agent(
            role='Aura (Restaurant AI Assistant)',
            goal='Validate orders, calculate costs, and summarize details.',
            backstory="You are Aura, the efficient AI front-desk for a restaurant...",
            tools=self.tools,
            llm=self.llm,  # <--- Passing the new LLM object here
            verbose=True
        )

    def process_order_task(self, user_order) -> Task:
        return Task(
            description=(
                f"1. Customer Order: '{user_order}'\n"
                "2. Fetch menu prices using the tool.\n"
                "3. Calculate total cost and estimated time.\n"
                "4. Check for Dine-in/Take-away."
            ),
            expected_output="Final summary with items, prices, total cost, and time.",
            agent=self.aura_agent()
        )

    def run(self, inputs):
        # Create and kick off the crew
        task = self.process_order_task(inputs['user_order'])
        crew = Crew(
            agents=[self.aura_agent()],
            tasks=[task],
            process=Process.sequential
        )
        return crew.kickoff()