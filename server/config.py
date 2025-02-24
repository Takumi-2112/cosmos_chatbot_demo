import os 
from dotenv import load_dotenv

load_dotenv()

AI_FOUNDRY_ENDPOINT = os.getenv("AI_FOUNDRY_ENDPOINT")
AI_FOUNDRY_DEPLOYMENT = os.getenv("AI_FOUNDRY_DEPLOYMENT")
AI_FOUNDRY_SUBSCRIPTION_KEY = os.getenv("AI_FOUNDRY_SUBSCRIPTION_KEY")