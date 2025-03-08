# import logging
# import traceback
# import asyncio
# import certifi
# import ssl
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from openai import AzureOpenAI, OpenAIError
# from azure.identity import DefaultAzureCredential
# from gremlin_python.driver import client, serializer
# from config import (
#     AI_FOUNDRY_ENDPOINT, AI_FOUNDRY_DEPLOYMENT, AI_FOUNDRY_KEY,
#     COSMOS_DB_ENDPOINT, COSMOS_DB_DATABASE, COSMOS_DB_GRAPH, COSMOS_DB_SECONDARY_KEY
# )

# app = FastAPI()

# # Allow all CORS (cross-origin requests)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # Only allow your frontend
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Initialize Azure AI Foundry (OpenAI)
# client_ai = AzureOpenAI(
#     azure_endpoint=AI_FOUNDRY_ENDPOINT,
#     api_key=AI_FOUNDRY_KEY,
#     api_version="2024-05-01-preview",
# )

# # Initialize SSL context for Cosmos DB
# ssl_context = ssl.create_default_context(cafile=certifi.where())

# # Initialize Gremlin Client for Cosmos DB
# gremlin_client = client.Client(
#     COSMOS_DB_ENDPOINT, 
#     'g',
#     username=f"/dbs/{COSMOS_DB_DATABASE}/colls/{COSMOS_DB_GRAPH}",
#     password=COSMOS_DB_SECONDARY_KEY,
#     message_serializer=serializer.GraphSONSerializersV2d0(),
#     ssl_context=ssl_context
# )

# # dont mind this mild debugging code 
# logger.debug(f"AI_FOUNDRY_ENDPOINT: {AI_FOUNDRY_ENDPOINT}")
# logger.debug(f"AI_FOUNDRY_DEPLOYMENT: {AI_FOUNDRY_DEPLOYMENT}")
# logger.debug(f"AI_FOUNDRY_KEY: {AI_FOUNDRY_KEY}")
# logger.debug(f"COSMOS_DB_ENDPOINT: {COSMOS_DB_ENDPOINT}")
# logger.debug(f"COSMOS_DB_DATABASE: {COSMOS_DB_DATABASE}")
# logger.debug(f"COSMOS_DB_GRAPH: {COSMOS_DB_GRAPH}")
# logger.debug(f"COSMOS_DB_SECONDARY_KEY: {COSMOS_DB_SECONDARY_KEY}")

# # Request model for chat messages
# class ChatRequest(BaseModel):
#     messages: list

# async def run_gremlin_query(query: str):
#     """
#     Executes a Gremlin query against Azure Cosmos DB Graph and returns the results as JSON-serializable data.
#     """
#     try:
#         future = await asyncio.to_thread(gremlin_client.submitAsync, query)
#         result = await asyncio.to_thread(future.result)  # Fetch the result

#         # Debugging: log the raw result
#         logger.debug(f"🪲🐞 Raw Gremlin query result: {result}")

#         # Process the result into a JSON-serializable format
#         processed_result = []
#         for item in result:
#             if hasattr(item, 'items'):  # If the item is a dictionary-like object
#                 processed_result.append(dict(item))
#             elif hasattr(item, 'id') and hasattr(item, 'label'):  # If the item is a vertex or edge
#                 processed_result.append({
#                     "id": item.id,
#                     "label": item.label,
#                     "properties": dict(item.properties) if hasattr(item, 'properties') else {}
#                 })
#             else:  # Fallback for other types (e.g., strings, numbers)
#                 processed_result.append(str(item))

#         return processed_result

#     except Exception as e:
#         logger.error(f"👹👹Error executing Gremlin query origin from run_gremlin_query function: {e}\n{traceback.format_exc()}")
#         return []


# async def generate_gremlin_query(request: ChatRequest):
#     """
#     Calls Azure AI Foundry to generate a Gremlin query based on the user's request.
#     """
#     try:
      
#         query_sharpener = {
#           "role": "user",
#           "content": [
#                 {
#               "type": "text",
#               "text": "*Search your chat_prompt array to extract the correct query, or use it as context to help you come up with the correct query*" 
#                 }
#             ]
#         }
        
#         request.messages.append(query_sharpener)
      
#         chat_prompt = [
#             {
#           "role": "system",
#           "content": [
#               {
#             "type": "text",
#             "text": "You are an expert at writing Gremlin queries for Azure Cosmos DB Graph that also uses the Groovy syntax.\n\nSchema:\n\n-Vertex (node) labels: Customers, SalesTransaction, Products, Pillars, Dates\n\n-Edges (relationships, links):\nCustomer -[CUSTOMER_TRANSACTION]-> SalesTransaction\nPillar -[PILLAR_FROM_TRANSACTION]-> SalesTransaction\nProduct -[PRODUCT_FROM_TRANSACTION]-> SalesTransaction\nDate -[TRANSACTION_DATE]-> SalesTransaction\n\n\nTable Properties:\n\nSalesTransaction has properties: sales_transaction_key, date_key, customer_key, pillar_key, product_key, dollar_cost, dollar_rev, dollar_profit, quantity\n\nCustomer has properties: customer_key, customer_name, location\n\nPillar has properties: pillar_key, pillar_name\n\nProduct has properties: product_key, product_name, manufacturer\n\nDate has properties: date_key, date_of_day, day, month, month_number, year\n\nBased on the question below, please ONLY return a valid Gremlin query for Azure Cosmos DB Graph that also uses the groovy syntax, NOTHING ELSE PLEASE:\n\nUser: \"Which pillar sold the most?\"\n\nAssistant: *Gremlin Query*"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Which pillar sold the most?\"\n\nUser: \"What is the highest-selling pillar?\"\n\nUser: \"Which pillar has the most sales?\"\n\nUser: “what pillar sold the most?”"
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.E().hasLabel('PILLAR_FROM_TRANSACTION')\n  .groupCount().by(outV().values('pillar_name'))\n  .order(local).by(values, decr)\n  .limit(local, 1)"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"I wish to see all the customers and their transactions\"\n\nUser: \"Show all customer transactions with the respective sales transactions\"\n\nUser: \"Show me a list of all customer transactions with the respective sales transactions\"\n\nUser: \"What are all the customer transactions along with their sales transaction?\"\n\nUser: \"Please give me a list of all the customers with their transactions\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.E().hasLabel('CUSTOMER_TRANSACTION').group().by(outV().values('customer_name')).by(inV().values('sales_transaction_key').fold())"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Show me the products that customer *insert ID* bought\"\n\nUser: \"Can I see all the products that customer *insert ID* bought?\"\n\nUser: \"I'm looking for the products that customer *insert ID* purchased\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Customer').has('customer_key', '50')\n  .out('CUSTOMER_TRANSACTION')\n  .in('PRODUCT_FROM_TRANSACTION')\n  .values('product_name')"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Show all transactions for customer with a specific ID.\"\n\nUser: \"Show the transactions for customer insert ID.\"\n\nUser: \"What are customer insert ID's transactions?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Customer') .has('customer_key', '{customer_key}') .out('CUSTOMER_TRANSACTION') .valueMap()"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Which city do we do business with the most?\"\n\nUser: \"Which city has the most transactions?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.E().hasLabel('CUSTOMER_TRANSACTION') .groupCount().by(outV().values('location')) .order(local).by(values, decr).limit(local, 1)"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Show me a list of all the cities in our database\"\n\nUser: \"Which cities do we have access to?\"\n\nUser: \"Which cities can we do business with\"\n\nUser: \"Provide me with a list of all the cities in our db\"\n\nUser: \"What are the cities in our db?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Customer').values('location').dedup()"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Which customer generates the highest average revenue per transaction?\"\n\nUser: \"Which customer has the highest average sales revenue?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Customer') .as('c') .out('CUSTOMER_TRANSACTION') .project('customer', 'avg_revenue') .by(select('c').values('customer_name')) .by(values('dollar_rev')) .group() .by(select('customer')) .by(mean(local)) .order(local).by(values, decr).limit(local, 1)"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Show me the transactions for product *insert ID*.\"\n\nUser: \"What are product *insert ID*'s transactions?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Product') .has('product_key', '{product_key}') .out('PRODUCT_FROM_TRANSACTION') .valueMap()"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Show me every customer with their respective purchased products.\"\n\nUser: \"What products did each customer buy?\"\n\nUser: \"Group together every client with the products they purchased.\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.V().hasLabel('Customer').as('c') .out('CUSTOMER_TRANSACTION') .in('PRODUCT_FROM_TRANSACTION') .values('product_name') .group() .by(select('c').values('customer_name')) .by(fold())"
#               }
#           ]
#             },
#             {
#           "role": "user",
#           "content": [
#               {
#             "type": "text",
#             "text": "User: \"Who is the customer with the most transactions?\"\n\nUser: \"Which client do we do business with the most?\"\n\nUser: \"What is the customer with the most transactions?\""
#               }
#           ]
#             },
#             {
#           "role": "assistant",
#           "content": [
#               {
#             "type": "text",
#             "text": "g.E().hasLabel('CUSTOMER_TRANSACTION').groupCount().by(outV().values('customer_name')).order(local).by(values, decr).limit(local, 1)"
#               }
#           ]
#             }
#         ]
        
#         chat_prompt.extend(request.messages)  # Add user messages

#         # Call AI Foundry (OpenAI) to generate a Gremlin query
#         response = client_ai.chat.completions.create(
#             model=AI_FOUNDRY_DEPLOYMENT,
#             messages=chat_prompt,
#             max_tokens=800,
#             temperature=0
#         )

#         # Debugging: log the AI Foundry response
#         logger.debug(f"AI Foundry response: {response}")

#         # Extract the Gremlin query
#         gremlin_query = response.choices[0].message.content.strip()

#         # Debugging: log the generated Gremlin query
#         logger.debug(f"Generated Gremlin query: {gremlin_query}")

#         return gremlin_query
#     except OpenAIError as e:
#         logger.error(f"🤖🤖Azure AI Foundry API error originating in generate_gremlin_query function: {e}\n{traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail="Azure AI Foundry API error.")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail="Internal server error.")

# @app.post("/chat_and_query")
# async def chat_and_query(request: ChatRequest):
#     """
#     Receives a user request, generates a Gremlin query using AI Foundry, 
#     executes the query on Cosmos DB, and returns the results.
#     """
#     try:
#         # Step 1: Generate Gremlin query from AI Foundry
#         gremlin_query = await generate_gremlin_query(request)

#         # Step 2: Run the generated Gremlin query
#         query_result = await run_gremlin_query(gremlin_query)

#         return {
#             "generated_query": gremlin_query,
#             "query_result": query_result
#         }

#     except HTTPException as e:
#         raise e  # If AI Foundry or Gremlin fails, return error
#     except Exception as e:
#         logger.error(f"❌❌chat_and_query function execution error: {e}\n{traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail="Internal server error.")