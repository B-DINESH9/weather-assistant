import asyncio
from unittest.mock import patch
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import GenerateContentResponse, Candidate, Content, Part
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
            if event.content and event.content.parts:
                response_text += "".join(part.text for part in event.content.parts if part.text)
                
        print(f"AGENT: {response_text.strip()}")

async def patched_generate_content(*args, **kwargs):
    contents = kwargs.get("contents")
    prompt = ""
    if isinstance(contents, str):
        prompt = contents
    elif isinstance(contents, list) and len(contents) > 0:
        if hasattr(contents[-1], "parts") and len(contents[-1].parts) > 0:
            prompt = contents[-1].parts[0].text
    
    query = prompt
    if "User query: '" in prompt:
        query = prompt.split("User query: '")[1].split("'")[0]
        
    is_shipping = "ship" in str(query).lower()
    
    if "Classify" in prompt or "Does the user query ask" in prompt:
        text = "SHIPPING" if is_shipping else "UNRELATED"
    else:
        text = "It costs $15 to ship a 5lb package to New York." if is_shipping else "I can't answer that."
        
    return GenerateContentResponse(
        candidates=[Candidate(content=Content(role="model", parts=[Part(text=text)]))],
        model_version="mock-model"
    )

async def patched_generate_content_stream(*args, **kwargs):
    resp = await patched_generate_content(*args, **kwargs)
    async def gen():
        yield resp
    return gen()

if __name__ == "__main__":
    with patch("google.genai.models.AsyncModels.generate_content", side_effect=patched_generate_content):
        with patch("google.genai.models.AsyncModels.generate_content_stream", side_effect=patched_generate_content_stream):
            asyncio.run(main())
