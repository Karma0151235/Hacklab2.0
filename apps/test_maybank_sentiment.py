#!/usr/bin/env python
"""
Direct test of Maybank sentiment analysis
Bypasses HTTP, tests the agent logic directly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.supervisor import SupervisorAgent
from agents.schemas import SupervisorInput
from agents.config import AgentConfig
from dotenv import load_dotenv

load_dotenv()

def test_maybank_sentiment():
    """Test sentiment analysis for Maybank"""
    print("=" * 70)
    print("SENTIMENT AGENT TEST: Maybank")
    print("=" * 70)

    # Check config
    print(f"\n[OK] Config Status:")
    print(f"  - USE_SENTIMENT_AGENT: {AgentConfig.USE_SENTIMENT_AGENT}")
    print(f"  - OpenRouter API Key: {'[OK] Set' if AgentConfig.OPENROUTER_API_KEY else '[FAIL] Missing'}")

    # Initialize supervisor
    print(f"\n[OK] Initializing Supervisor Agent...")
    try:
        supervisor = SupervisorAgent()
        print(f"  - Supervisor initialized")
        print(f"  - RAG Agent ready")
        print(f"  - Financial Agent ready")
        print(f"  - Alert Agent ready")
        print(f"  - Sentiment Agent ready")
    except Exception as e:
        print(f"[FAIL] Error initializing supervisor: {e}")
        return

    # Run query
    query = "What is the market sentiment for Maybank?"
    print(f"\n[OK] Running Query: '{query}'")
    print(f"\n  Processing...\n")

    try:
        result = supervisor.process(
            SupervisorInput(query=query),
            progress_callback=_print_progress
        )

        print(f"\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        # Basic info
        print(f"\nAnswer (first 300 chars):")
        print(f"  {result.answer[:300]}...")

        print(f"\nAgents Used: {result.agents_used}")
        print(f"Confidence Score: {result.confidence_score:.1%}")
        print(f"Processing Steps: {len(result.steps)}")

        # Sentiment specific
        if result.sentiment:
            print(f"\n" + "-" * 70)
            print("SENTIMENT ANALYSIS OUTPUT")
            print("-" * 70)
            print(f"\nOverall Sentiment: {result.sentiment.overall_sentiment.upper()}")
            print(f"Sentiment Score: {result.sentiment.sentiment_score:.2f} (range -1.0 to 1.0)")
            print(f"Confidence: {result.sentiment.confidence:.1%}")
            print(f"Trend: {result.sentiment.trend}")
            print(f"Articles Analyzed: {result.sentiment.articles_analyzed}")

            if result.sentiment.summary:
                print(f"\nSummary:\n  {result.sentiment.summary}")

            if result.sentiment.key_topics:
                print(f"\nKey Topics: {', '.join(result.sentiment.key_topics)}")

            if result.sentiment.key_phrases:
                print(f"\nKey Phrases: {', '.join(result.sentiment.key_phrases[:5])}")

            if result.sentiment.sentiment_by_source:
                print(f"\nSentiment by Source:")
                for source, score in result.sentiment.sentiment_by_source.items():
                    sentiment_label = "+" if score > 0.2 else "-" if score < -0.2 else "~"
                    print(f"  {source}: {sentiment_label} {score:.2f}")
        else:
            print(f"\n[WARN] No sentiment output found")

        print(f"\n" + "=" * 70)
        print("[SUCCESS] TEST COMPLETE")
        print("=" * 70)

    except Exception as e:
        import traceback
        print(f"\n[FAIL] Error processing query: {e}")
        traceback.print_exc()

def _print_progress(event):
    """Print progress events"""
    agent_id = event.get("agent_id", "?")
    status = event.get("status", "?")
    message = event.get("message", "")

    if status == "running":
        print(f"  [>] [{agent_id}] {message}")
    elif status == "completed":
        print(f"  [+] [{agent_id}] {message}")
    elif status == "skipped":
        print(f"  [~] [{agent_id}] {message}")
    elif status == "error":
        print(f"  [!] [{agent_id}] {message}")

if __name__ == "__main__":
    test_maybank_sentiment()
