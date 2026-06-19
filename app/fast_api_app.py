# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
import logging as std_logging

# Configure Vertex AI vs. Gemini Developer API (AI Studio)
if os.environ.get("GEMINI_API_KEY") and os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") is None:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

project_id = None
logger = None

if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true":
    try:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
        logging_client = google_cloud_logging.Client()
        logger = logging_client.logger(__name__)
    except Exception:
        if os.environ.get("GEMINI_API_KEY"):
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
        else:
            raise

if logger is None:
    std_logging.basicConfig(level=std_logging.INFO)
    class LocalLogger:
        def log_struct(self, info_dict, severity="INFO"):
            std_logging.info(f"[{severity}] {info_dict}")
    logger = LocalLogger()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

# Enable Cloud telemetry only when running in Vertex mode
otel_to_cloud = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=otel_to_cloud,
)
app.title = "weather-assistant"
app.description = "API for interacting with the Agent weather-assistant"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
