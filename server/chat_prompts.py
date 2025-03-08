chat_prompt = [
            {
          "role": "system",
          "content": [
              {
            "type": "text",
            "text": "You are an expert at writing Gremlin queries for Azure Cosmos DB Graph that also uses the Groovy syntax.\n\nSchema:\n\n-Vertex (node) labels: Customers, SalesTransaction, Products, Pillars, Dates\n\n-Edges (relationships, links):\nCustomer -[CUSTOMER_TRANSACTION]-> SalesTransaction\nPillar -[PILLAR_FROM_TRANSACTION]-> SalesTransaction\nProduct -[PRODUCT_FROM_TRANSACTION]-> SalesTransaction\nDate -[TRANSACTION_DATE]-> SalesTransaction\n\n\nTable Properties:\n\nSalesTransaction has properties: sales_transaction_key, date_key, customer_key, pillar_key, product_key, dollar_cost, dollar_rev, dollar_profit, quantity\n\nCustomer has properties: customer_key, customer_name, location\n\nPillar has properties: pillar_key, pillar_name\n\nProduct has properties: product_key, product_name, manufacturer\n\nDate has properties: date_key, date_of_day, day, month, month_number, year\n\nBased on the question below, please ONLY return a valid Gremlin query for Azure Cosmos DB Graph that also uses the groovy syntax, NOTHING ELSE PLEASE:\n\nUser: \"Which pillar sold the most?\"\n\nAssistant: *Gremlin Query*"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Which pillar sold the most?\"\n\nUser: \"What is the highest-selling pillar?\"\n\nUser: \"Which pillar has the most sales?\"\n\nUser: “what pillar sold the most?”"
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.E().hasLabel('PILLAR_FROM_TRANSACTION')\n  .groupCount().by(outV().values('pillar_name'))\n  .order(local).by(values, decr)\n  .limit(local, 1)"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Which product sold the most?\"\n\nUser: \"What is the highest-selling product?\"\n\nUser: \"Which product has the most sales?\"\n\nUser: “what product sold the most?”"
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.E().hasLabel('PRODUCT_FROM_TRANSACTION')\n  .groupCount().by(outV().values('product_name'))\n  .order(local).by(values, decr)\n  .limit(local, 1)"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"I wish to see all the customers and their transactions\"\n\nUser: \"Show all customer transactions with the respective sales transactions\"\n\nUser: \"Show me a list of all customer transactions with the respective sales transactions\"\n\nUser: \"What are all the customer transactions along with their sales transaction?\"\n\nUser: \"Please give me a list of all the customers with their transactions\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.E().hasLabel('CUSTOMER_TRANSACTION').group().by(outV().values('customer_name')).by(inV().values('sales_transaction_key').fold())"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Show me the products that customer *insert ID* bought\"\n\nUser: \"Can I see all the products that customer *insert ID* bought?\"\n\nUser: \"I'm looking for the products that customer *insert ID* purchased\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Customer').has('customer_key', '50')\n  .out('CUSTOMER_TRANSACTION')\n  .in('PRODUCT_FROM_TRANSACTION')\n  .values('product_name')"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Show all transactions for customer with a specific ID.\"\n\nUser: \"Show the transactions for customer insert ID.\"\n\nUser: \"What are customer insert ID's transactions?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Customer') .has('customer_key', '{customer_key}') .out('CUSTOMER_TRANSACTION') .valueMap()"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Which city do we do business with the most?\"\n\nUser: \"Which city has the most transactions?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.E().hasLabel('CUSTOMER_TRANSACTION') .groupCount().by(outV().values('location')) .order(local).by(values, decr).limit(local, 1)"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Show me a list of all the cities in our database\"\n\nUser: \"Which cities do we have access to?\"\n\nUser: \"Which cities can we do business with\"\n\nUser: \"Provide me with a list of all the cities in our db\"\n\nUser: \"What are the cities in our db?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Customer').values('location').dedup()"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Which customer generates the highest average revenue per transaction?\"\n\nUser: \"Which customer has the highest average sales revenue?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Customer') .as('c') .out('CUSTOMER_TRANSACTION') .project('customer', 'avg_revenue') .by(select('c').values('customer_name')) .by(values('dollar_rev')) .group() .by(select('customer')) .by(mean(local)) .order(local).by(values, decr).limit(local, 1)"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Show me the transactions for product *insert ID*.\"\n\nUser: \"What are product *insert ID*'s transactions?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Product') .has('product_key', '{product_key}') .out('PRODUCT_FROM_TRANSACTION') .valueMap()"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Show me every customer with their respective purchased products.\"\n\nUser: \"What products did each customer buy?\"\n\nUser: \"Group together every client with the products they purchased.\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.V().hasLabel('Customer').as('c') .out('CUSTOMER_TRANSACTION') .in('PRODUCT_FROM_TRANSACTION') .values('product_name') .group() .by(select('c').values('customer_name')) .by(fold())"
              }
          ]
            },
            {
          "role": "user",
          "content": [
              {
            "type": "text",
            "text": "User: \"Who is the customer with the most transactions?\"\n\nUser: \"Which client do we do business with the most?\"\n\nUser: \"What is the customer with the most transactions?\""
              }
          ]
            },
            {
          "role": "assistant",
          "content": [
              {
            "type": "text",
            "text": "g.E().hasLabel('CUSTOMER_TRANSACTION').groupCount().by(outV().values('customer_name')).order(local).by(values, decr).limit(local, 1)"
              }
          ]
            }
        ]