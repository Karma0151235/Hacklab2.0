
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from agents.supervisor import SupervisorAgent
from agents.schemas import SupervisorInput
from etl.logging_config import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

def test_sentiment_flow():
    agent = SupervisorAgent()
    
    query = "What is the market sentiment for Maybank?"
    print(f"\nRunning query: {query}")
    
    try:
        result = agent.process(SupervisorInput(query=query))
        
        print("\n=== Result ===")
        print(f"Answer: {result.answer[:200]}...")
        print(f"Agents Used: {result.agents_used}")
        
        if result.sentiment:
            print("\n=== Sentiment Output ===")
            print(f"Overall: {result.sentiment.overall_sentiment}")
            print(f"Score: {result.sentiment.sentiment_score}")
            print(f"Summary: {result.sentiment.summary}")
            print(f"Articles Analyzed: {result.sentiment.articles_analyzed}")
        else:
            print("\n❌ No sentiment output found!")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sentiment_flow()
