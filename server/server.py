import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI, OpenAIError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from config import AI_FOUNDRY_ENDPOINT, AI_FOUNDRY_DEPLOYMENT, AI_FOUNDRY_SUBSCRIPTION_KEY

app = FastAPI()

# Allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, you can specify specific domains here if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Azure AI Foundry Configuration
ENDPOINT = AI_FOUNDRY_ENDPOINT  # Azure AI Foundry endpoint
DEPLOYMENT = AI_FOUNDRY_DEPLOYMENT  # Azure AI Foundry deployment
subscription_key = AI_FOUNDRY_SUBSCRIPTION_KEY  # Azure AI Foundry subscription key

# Initialize the Azure OpenAI client with subscription key-based authentication
client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=subscription_key,  # Pass the subscription key
    api_version="2024-05-01-preview",  # Ensure you're using the correct version
)

# ChatRequest model
class ChatRequest(BaseModel):
    messages: list

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Prepare the chat prompt based on the received messages (as in AI Foundry example)
        chat_prompt = [
    {
        "role": "system",
         "content": "You are an expert at writing Gremlin queries for Azure Cosmos DB Graph that also uses the groovy syntax.\n\nThe schema is:\n\n  - Vertex (node) labels: Customers, SalesTransaction, Products, Pillars, Dates\n\n  - Edges (relationships, links): Customer -[CUSTOMER_TRANSACTION]->SalesTransaction, Pillar -[PILLAR_FROM_TRANSACTION]->SalesTransaction, Product -[PRODUCT_FROM_TRANSACTION]->SalesTransaction, Date -[TRANSACTION_DATE]->SalesTransaction\n\n  - The SalesTransaction Table has properties: sales_transaction_key,date_key,customer_key,pillar_key,product_key,dollar_cost,dollar_rev,dollar_profit,quantity\n\n  - The Customer Table has properties: customer_key,customer_name,location\n\n- The Pilllar Table has properties: pillar_key,pillar_name\n\n- The Product Table has properties: product_key,product_name,manufacturer\n\n- The Date Table has properties: date_key,date_of_day,day,month,month_number,year\n\nBased on the question below, please ONLY return a valid Gremlin query for Azure Cosmos DB Graph that also uses the groovy syntax, NOTHING ELSE PLEASE:\n\nUser: \"Which pillar sold the most?\"\n\nAssistant: *Query*\n\n"
    },
    {
        "role": "user",
        "content": "User: \"which pillar sold the most?\"\n\nUser: \"what is the highest selling pillar?\"\n\nUser: \"which pillar has the most sales?\""
    },
    {
        "role": "assistant",
        "content": "g.E().hasLabel('PILLAR_FROM_TRANSACTION').groupCount().by(outV().values('pillar_name')).order(local).by(values, decr).limit(local, 1)"
    },
    {
        "role": "user",
        "content": "User: \"Show all customer transactions with the respective sales transactions\"\n\nUser: \"What are all the customer transactions along with their sales transaction\""
    },
    {
        "role": "assistant",
        "content": "g.E().hasLabel('CUSTOMER_TRANSACTION').group().by(outV().values('customer_name')).by(inV().values('sales_transaction_key').fold())"
    },
    {
        "role": "user",
        "content": "User: \"Which city do we do business with the most?\""
    },
    {
        "role": "assistant",
        "content": "g.E().hasLabel('CUSTOMER_TRANSACTION').groupCount().by(outV().values('location')).order(local).by(values, decr)"
    },
    {
        "role": "user",
        "content": "User: \"Show all transactions for customer with a specific ID\"\n\nUser: \"Show the transactions for customer *insert ID*\"\n\nUser: \"What are customer *insert ID*'s transactions?\""
    },
    {
        "role": "assistant",
        "content": "g.V().hasLabel('Customer').has('customer_key', '{customer_key}').out('CUSTOMER_TRANSACTION').valueMap()"
    },
    {
        "role": "user",
        "content": "User: \"Which customer generates the highest average revenue per transaction?\"\n\nUser: \"Which customer has the highest average sales revenue?\"\n"
    },
    {
        "role": "assistant",
        "content": "g.V().hasLabel('Customer')\n  .as('c')\n  .out('CUSTOMER_TRANSACTION')\n  .project('customer', 'avg_revenue')\n    .by(select('c').values('customer_name'))  \n    .by(values('dollar_rev'))  \n  .group()\n    .by(select('customer'))\n    .by(mean(local))\n  .order(local).by(values, decr)"
    },
    {
        "role": "user",
        "content": "User: \"Show me the transactions for product *insert ID*\"\n\nUser: \"What are product *insert ID*'s  transactions\""
    },
    {
        "role": "assistant",
        "content": "g.V().hasLabel('Product').has('product_key', '{product_key}').out('PRODUCT_FROM_TRANSACTION').valueMap()"
    },
    {
        "role": "user",
        "content": "User: \"Show me every customer with their respective purchased products\"\n\nUser: \"What products did each customer buy?\"\n\nUser: \"Group together every client with the products they purchased\""
    },
    {
        "role": "assistant",
        "content": "g.V().hasLabel('Customer').as('c')  \n  .out('CUSTOMER_TRANSACTION')  \n  .in('PRODUCT_FROM_TRANSACTION')  \n  .values('product_name')  \n  .group()  \n    .by(select('c').values('customer_name'))  \n    .by(fold())"
    },
    {
        "role": "user",
        "content": ""
    },
    {
        "role": "assistant",
        "content": ""
    }
] 

        # Combine the received messages with the pre-existing prompts for context
        chat_prompt.extend(request.messages)

        # Make the API call to get a response from Azure OpenAI
        response = client.chat.completions.create(
          model=DEPLOYMENT,
          messages=chat_prompt,
          max_tokens=800,  
          temperature=0.7,  
          top_p=0.95,  
          frequency_penalty=0,  
          presence_penalty=0,
          stop=None,  
          stream=False
        )

        # Return the reply from the assistant (same as Azure AI Foundry example)
        return {"reply": response.choices[0].message.content}

    except OpenAIError as e:
        logger.error(f"Azure OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail="Azure OpenAI API error.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")