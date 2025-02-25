import logging
import asyncio
import certifi
import ssl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI, OpenAIError
from azure.identity import DefaultAzureCredential
from gremlin_python.driver import client, serializer
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
logging.basicConfig(level=logging.ERROR)
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
        logger.error(f"Error executing Gremlin query: {e}")
        return []


async def generate_gremlin_query(request: ChatRequest):
    """
    Calls Azure AI Foundry to generate a Gremlin query based on the user's request.
    """
    try:
        chat_prompt = [
            {
          "role": "system",
          "content": "You are an expert at writing Gremlin queries for Azure Cosmos DB Graph that also uses the Groovy syntax. YOU ARE TO NEVER ANSWER WITH ANYTHING BUT GREMLIN QUERIES.\n\nSchema:\n\n-Vertex (node) labels: Customers, SalesTransaction, Products, Pillars, Dates\n\n-Edges (relationships, links):\nCustomer -[CUSTOMER_TRANSACTION]-> SalesTransaction\nPillar -[PILLAR_FROM_TRANSACTION]-> SalesTransaction\nProduct -[PRODUCT_FROM_TRANSACTION]-> SalesTransaction\nDate -[TRANSACTION_DATE]-> SalesTransaction\n\n\nTable Properties:\n\nSalesTransaction has properties: sales_transaction_key, date_key, customer_key, pillar_key, product_key, dollar_cost, dollar_rev, dollar_profit, quantity\n\nCustomer has properties: customer_key, customer_name, location\n\nPillar has properties: pillar_key, pillar_name\n\nProduct has properties: product_key, product_name, manufacturer\n\nDate has properties: date_key, date_of_day, day, month, month_number, year\n\nBased on the question below, please ONLY return a valid Gremlin query for Azure Cosmos DB Graph that also uses the groovy syntax",
            },
            {
          "role": "user",
          "content": "User: \"Which pillar is most sold?\"\n\nUser: \"What is the highest-selling pillar?\"\n\nUser: \"Which pillar has the most sales?\"\n\nUser: \"Hello how can i find the most sold pillar?\""
            },
            {
          "role": "assistant",
          "content": "g.E().hasLabel('PILLAR_FROM_TRANSACTION')\n  .groupCount().by(outV().values('pillar_name'))\n  .order(local).by(values, decr)\n  .limit(local, 1)"
            },
            {
          "role": "user",
          "content": "User: \"Show all customer transactions with the respective sales transactions.\"\n\nUser: \"What are all the customer transactions along with their sales transaction?\""
            },
            {
          "role": "assistant",
          "content": "g.E().hasLabel('CUSTOMER_TRANSACTION')\n  .group()\n  .by(outV().values('customer_name'))\n  .by(inV().values('sales_transaction_key').fold())"
            },
            {
          "role": "user",
          "content": "User: \"Which city do we do business with the most?\"\n\nUser: \"Which city has the most transactions?\""
            },
            {
          "role": "assistant",
          "content": "g.E().hasLabel('CUSTOMER_TRANSACTION')\n  .groupCount().by(outV().values('location'))\n  .order(local).by(values, decr).limit(local, 1)"
            },
            {
          "role": "user",
          "content": "User: \"Show all transactions for customer with a specific ID.\"\n\nUser: \"Show the transactions for customer *insert ID*.\"\n\nUser: \"What are customer *insert ID*'s transactions?\""
            },
            {
          "role": "assistant",
          "content": "g.V().hasLabel('Customer')\n  .has('customer_key', '{customer_key}')\n  .out('CUSTOMER_TRANSACTION')\n  .valueMap()"
            },
            {
          "role": "user",
          "content": "User: \"Which customer generates the highest average revenue per transaction?\"\n\nUser: \"Which customer has the highest average sales revenue?\""
            },
            {
          "role": "assistant",
          "content": "g.V().hasLabel('Customer')\n  .as('c')\n  .out('CUSTOMER_TRANSACTION')\n  .project('customer', 'avg_revenue')\n    .by(select('c').values('customer_name'))  \n    .by(values('dollar_rev'))  \n  .group()\n    .by(select('customer'))\n    .by(mean(local))\n  .order(local).by(values, decr).limit(local, 1)"
            },
            {
          "role": "user",
          "content": "User: \"Show me the transactions for product insert ID.\"\n\nUser: \"What are product *insert ID*'s transactions?\""
            },
            {
          "role": "assistant",
          "content": "g.V().hasLabel('Product')\n  .has('product_key', '{product_key}')\n  .out('PRODUCT_FROM_TRANSACTION')\n  .valueMap()"
            },
            {
          "role": "user",
          "content": "User: \"Show me every customer with their respective purchased products.\"\n\nUser: \"What products did each customer buy?\"\n\nUser: \"Group together every client with the products they purchased.\""
            },
            {
          "role": "assistant",
          "content": "g.V().hasLabel('Customer').as('c')  \n  .out('CUSTOMER_TRANSACTION')  \n  .in('PRODUCT_FROM_TRANSACTION')  \n  .values('product_name')  \n  .group()  \n    .by(select('c').values('customer_name'))  \n    .by(fold())"
            },
            {
          "role": "user",
          "content": "User: \"Who is the customer with the most transactions?\"\n\nUser: \"Which client do we do business with the most?\"\n\nUser: \"What is the customer with the most transactions?\""
            },
            {
          "role": "assistant",
          "content": "g.E().hasLabel('CUSTOMER_TRANSACTION').groupCount().by(outV().values('customer_name')).order(local).by(values, decr).limit(local, 1)"
            }
        ]
        
        chat_prompt.extend(request.messages)  # Add user messages

        # Call AI Foundry (OpenAI) to generate a Gremlin query
        response = client_ai.chat.completions.create(
            model=AI_FOUNDRY_DEPLOYMENT,
            messages=chat_prompt,
            max_tokens=300,
            temperature=0.5
        )

        # Debugging: log the AI Foundry response
        logger.debug(f"AI Foundry response: {response}")

        # Extract the Gremlin query
        gremlin_query = response.choices[0].message.content.strip()

        # Debugging: log the generated Gremlin query
        logger.debug(f"Generated Gremlin query: {gremlin_query}")

        return gremlin_query
    except OpenAIError as e:
        logger.error(f"Azure AI Foundry API error: {e}")
        raise HTTPException(status_code=500, detail="Azure AI Foundry API error.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.post("/chat_and_query")
async def chat_and_query(request: ChatRequest):
    """
    Receives a user request, generates a Gremlin query using AI Foundry, 
    executes the query on Cosmos DB, and returns the results.
    """
    try:
        # Step 1: Generate Gremlin query from AI Foundry
        gremlin_query = await generate_gremlin_query(request)

        # Step 2: Run the generated Gremlin query
        query_result = await run_gremlin_query(gremlin_query)

        return {
            "generated_query": gremlin_query,
            "query_result": query_result
        }

    except HTTPException as e:
        raise e  # If AI Foundry or Gremlin fails, return error
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
