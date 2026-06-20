import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

async def main():
    session_service = InMemorySessionService()
    
    queries = [
        "How much does it cost to ship a 5lb package to New York?",
        "What is the capital of France?"
    ]
    
    for query in queries:
        print(f"\n---")
        print(f"USER: {query}")
        session = await session_service.create_session(user_id="demo_user", app_name="demo")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="demo")
        
        message = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            new_message=message,
            user_id="demo_user",
            session_id=session.id,
        ):
            if hasattr(event, "output") and isinstance(event.output, str):
                response_text = event.output
            elif event.content and event.content.parts:
                response_text += "".join(part.text for part in event.content.parts if part.text)
                
        print(f"AGENT: {response_text.strip()}")

if __name__ == "__main__":
    asyncio.run(main())
