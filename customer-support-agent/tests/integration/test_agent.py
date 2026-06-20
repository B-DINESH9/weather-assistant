from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

def test_shipping_query_routing() -> None:
    """Verify that shipping-related queries are routed correctly and answered."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="How much does it cost to ship a 5lb package to New York?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0

    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            response_text += "".join(part.text for part in event.content.parts if part.text)
            
    assert "cost" in response_text.lower() or "ship" in response_text.lower() or "rate" in response_text.lower()
    assert "sorry" not in response_text.lower()

def test_unrelated_query_routing() -> None:
    """Verify that unrelated queries are routed to the polite decline node."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="What is the capital of France?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0

    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            response_text += "".join(part.text for part in event.content.parts if part.text)

    assert "sorry" in response_text.lower()
    assert "shipping" in response_text.lower()
