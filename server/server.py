import logging
import traceback
import asyncio
import certifi
import json
import ssl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI, OpenAIError
from azure.identity import DefaultAzureCredential
from gremlin_python.driver import client, serializer
from chat_prompts import chat_prompt
from config import (
    AI_FOUNDRY_ENDPOINT, AI_FOUNDRY_DEPLOYMENT, AI_FOUNDRY_KEY,
    COSMOS_DB_ENDPOINT, COSMOS_DB_DATABASE, COSMOS_DB_GRAPH, COSMOS_DB_PRIMARY_KEY
)

app = FastAPI()

# Allow all CORS (cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Only allow your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Azure AI Foundry (OpenAI)
client_ai = AzureOpenAI(
    azure_endpoint=AI_FOUNDRY_ENDPOINT,
    api_key=AI_FOUNDRY_KEY,
    api_version="2024-05-01-preview",
)

# Initialize SSL context for Cosmos DB
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Initialize Gremlin Client for Cosmos DB
gremlin_client = client.Client(
    COSMOS_DB_ENDPOINT, 
    'g',
    username=f"/dbs/{COSMOS_DB_DATABASE}/colls/{COSMOS_DB_GRAPH}",
    password=COSMOS_DB_PRIMARY_KEY,
    message_serializer=serializer.GraphSONSerializersV2d0(),
    ssl_context=ssl_context
)

# dont mind this mild debugging code 
logger.debug(f"AI_FOUNDRY_ENDPOINT: {AI_FOUNDRY_ENDPOINT}")
logger.debug(f"AI_FOUNDRY_DEPLOYMENT: {AI_FOUNDRY_DEPLOYMENT}")
logger.debug(f"AI_FOUNDRY_KEY: {AI_FOUNDRY_KEY}")
logger.debug(f"COSMOS_DB_ENDPOINT: {COSMOS_DB_ENDPOINT}")
logger.debug(f"COSMOS_DB_DATABASE: {COSMOS_DB_DATABASE}")
logger.debug(f"COSMOS_DB_GRAPH: {COSMOS_DB_GRAPH}")
logger.debug(f"COSMOS_DB_PRIMARY_KEY: {COSMOS_DB_PRIMARY_KEY}")

# Request model for chat messages
class ChatRequest(BaseModel):
    messages: list

async def run_gremlin_query(query: str):
    """
    Executes a Gremlin query against Azure Cosmos DB Graph and returns the results as JSON-serializable data.
    """
    try:
        future = await asyncio.to_thread(gremlin_client.submitAsync, query)
        result = await asyncio.to_thread(future.result)  # Fetch the result

        # Debugging: log the raw result
        logger.debug(f"🪲🐞 Raw Gremlin query result: {result}")

        # Process the result into a JSON-serializable format
        processed_result = []
        for item in result:
            if hasattr(item, 'items'):  # If the item is a dictionary-like object
                processed_result.append(dict(item))
            elif hasattr(item, 'id') and hasattr(item, 'label'):  # If the item is a vertex or edge
                processed_result.append({
                    "id": item.id,
                    "label": item.label,
                    "properties": dict(item.properties) if hasattr(item, 'properties') else {}
                })
            else:  # Fallback for other types (e.g., strings, numbers)
                processed_result.append(str(item))

        return processed_result

    except Exception as e:
        logger.error(f"👹👹Error executing Gremlin query origin from run_gremlin_query function: {e}\n{traceback.format_exc()}")
        return []


async def generate_gremlin_query(request: ChatRequest):
    """
    Calls Azure AI Foundry to generate a Gremlin query based on the user's request.
    """
    try:
        query_sharpener = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "*Search your chat_prompt array to extract the correct query, or use it as context to help you come up with the correct query*" 
                }
            ]
        }

        # Create a fresh copy of the chat_prompt to avoid modifying the global list
        chat_context = chat_prompt.copy()  # Ensure global chat_prompt remains unchanged
        chat_context.extend(request.messages)  # Add user messages locally
        chat_context.append(query_sharpener)  # Append query refinement instruction

        # Call AI Foundry (OpenAI) to generate a Gremlin query
        response = client_ai.chat.completions.create(
            model=AI_FOUNDRY_DEPLOYMENT,
            messages=chat_context,  # Use local context, not the global one
            max_tokens=800,
            temperature=0
        )

        # Debugging: log the AI Foundry response
        logger.debug(f"AI Foundry response: {response}")

        # Extract the Gremlin query
        gremlin_query = response.choices[0].message.content.strip()

        # Debugging: log the generated Gremlin query
        logger.debug(f"Generated Gremlin query: {gremlin_query}")

        return gremlin_query
    except OpenAIError as e:
        logger.error(f"🤖🤖Azure AI Foundry API error originating in generate_gremlin_query function: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Azure AI Foundry API error.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error.")



async def generate_humanized_response(user_prompt: str, json_data: list):
    """
    Calls Azure AI Foundry to convert JSON data into a human-friendly response.
    """
    try:
        # Format the JSON data as a readable string
        json_text = f"JSON Data:\n{json.dumps(json_data, indent=2)}"

        # AI Foundry request to convert JSON into a natural response
        response = client_ai.chat.completions.create(
            model=AI_FOUNDRY_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an AI assistant that turns structured JSON data into human-friendly responses. For example, if you get something like '['[{' Resource placement': 18}]' ]' you can return smething like Resource placement is the highest with 18 sales transactions"},
                {"role": "user", "content": f"User Query: {user_prompt}\n{json_text}\n\nuse the user_prompt for context on generating a user friendly response with json_text."}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # Extract AI response
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        logger.error(f"Error in generate_humanized_response: {e}\n{traceback.format_exc()}")
        return "I'm sorry, but I couldn't generate a response."

    except Exception as e:
        logger.error(f"Unexpected error in generate_humanized_response: {e}\n{traceback.format_exc()}")
        return "There was an issue processing your request."
      

@app.post("/chat_and_query")
async def chat_and_query(request: ChatRequest):
    """
    Receives a user request, generates a Gremlin query using AI Foundry, 
    executes the query on Cosmos DB, and returns a humanized response.
    """
    try:
        # Step 1: Generate Gremlin query from AI Foundry
        gremlin_query = await generate_gremlin_query(request)

        # Step 2: Execute the Gremlin query on Cosmos DB
        query_result = await run_gremlin_query(gremlin_query)

        # Step 3: Convert JSON to humanized text
        humanized_response = await generate_humanized_response(request.messages[-1]["content"], query_result)

        return {
          "generated_query": gremlin_query,
          "query_result": query_result,
          "response": humanized_response,             
          "raw_data": query_result
          }

    except HTTPException as e:
        raise e  # If AI Foundry or Gremlin fails, return error
    except Exception as e:
        logger.error(f"❌❌chat_and_query function execution error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error.")