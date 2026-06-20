# ruff: noqa
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
from google.adk import Context, Workflow
from google.adk.apps import App
from google.adk.workflow import START, node
from groq import AsyncGroq

# Initialize Groq client
# User must have GROQ_API_KEY environment variable set
groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# We will use llama-3.1-8b-instant as the model, which is blazingly fast on Groq
GROQ_MODEL = "llama-3.1-8b-instant"

# 1. Define the classification node
@node
async def classify_query(ctx: Context, node_input: str) -> str:
    prompt = f"""
    You are a classification assistant. 
    Classify the following user query into exactly one of these two categories:
    - 'shipping': If the user is asking about shipping, delivery, or tracking.
    - 'unrelated': If the query is about anything else.

    Return ONLY the category name. Do not include any other text.

    User query: '{node_input}'
    """
    
    response = await groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0,
    )
    
    category = response.choices[0].message.content.strip().lower()
    
    if "shipping" in category:
        ctx.route = "shipping"
    else:
        ctx.route = "unrelated"
        
    return node_input

# 2. Define the shipping assistant node (Replaces the ADK Agent to use Groq)
@node
async def shipping_faq_agent(ctx: Context, node_input: str) -> str:
    system_prompt = "You are a playful, enthusiastic customer support assistant that specializes in answering shipping and delivery questions. Use emojis in your responses! Keep your answers concise but fun, and be sure to highlight the free shipping threshold! 📦✨🎉"
    
    response = await groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": node_input}
        ],
        model=GROQ_MODEL,
        temperature=0.3,
    )
    
    return response.choices[0].message.content.strip()

# 3. Define the polite decline node
@node
async def polite_decline(ctx: Context, node_input: str) -> str:
    return "I'm sorry, but I can only answer questions related to shipping (rates, tracking, delivery, returns). Please let me know how I can help you with those!"

# 4. Assemble the Workflow Graph
root_agent = Workflow(
    name="customer_support_workflow",
    edges=[
        # START triggers the classification node
        (START, classify_query),
        # Route classification to either the shipping FAQ agent or the polite decline node
        (classify_query, {
            "shipping": shipping_faq_agent,
            "unrelated": polite_decline,
        }),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
