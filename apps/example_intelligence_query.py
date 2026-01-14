#!/usr/bin/env python3
"""
Example usage of Market Intelligence System
Demonstrates how to query the system and process responses
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from workflows import run_intelligence_query
from etl.logging_config import get_logger

logger = get_logger(__name__)


def print_separator(title: str = ""):
    """Print a visual separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_output(output):
    """Pretty print the output"""

    print_separator("ANSWER")
    print(output.answer)

    print_separator("AGENTS USED")
    print(", ".join(output.agents_used))

    if output.steps:
        print_separator("REASONING STEPS")
        for i, step in enumerate(output.steps, 1):
            print(f"{i}. {step}")

    if output.citations:
        print_separator("CITATIONS")
        for i, citation in enumerate(output.citations, 1):
            print(f"\n[{i}] {citation.filename}")
            print(f"    Company: {citation.company_name}")
            print(f"    Collection: {citation.collection}")
            if citation.page_number:
                print(f"    Page: {citation.page_number}")
            print(f"    Confidence: {citation.confidence_score:.2f}")

    if output.table_data:
        print_separator("TABLE DATA")
        print(f"Filename: {output.table_data.get('filename')}")
        print(f"Company: {output.table_data.get('company_name')}")
        print(f"\nTable (first 5 rows):")
        for i, row in enumerate(output.table_data.get('data', [])[:5]):
            print(f"  {row}")

    print_separator("METADATA")
    print(f"Confidence Score: {output.confidence_score:.2f}")
    print(f"Agents Used: {len(output.agents_used)}")
    print(f"Citations: {len(output.citations)}")
    print(f"Steps: {len(output.steps)}")


def example_queries():
    """Run example queries"""

    # Example 1: Financial metrics query
    print_separator("EXAMPLE 1: Financial Metrics Query")
    query1 = "What are the key financial metrics for Foodie Media Berhad? Calculate profitability and liquidity ratios."

    print(f"\nQuery: {query1}\n")
    print("Processing...")

    output1 = run_intelligence_query(query1)
    print_output(output1)

    # Example 2: Risk and alerts query
    print_separator("\n\nEXAMPLE 2: Risk and Alerts Query")
    query2 = "Are there any financial concerns or risks for SEMICO? Check for threshold breaches and adverse indicators."

    print(f"\nQuery: {query2}\n")
    print("Processing...")

    output2 = run_intelligence_query(query2)
    print_output(output2)

    # Example 3: General information query
    print_separator("\n\nEXAMPLE 3: General Information Query")
    query3 = "What is the latest quarterly revenue for companies in the database?"

    print(f"\nQuery: {query3}\n")
    print("Processing...")

    output3 = run_intelligence_query(query3)
    print_output(output3)


def interactive_mode():
    """Interactive query mode"""
    print_separator("INTERACTIVE MODE")
    print("Enter your queries (type 'exit' to quit)")
    print("="*80)

    while True:
        try:
            query = input("\n\nQuery: ").strip()

            if not query:
                continue

            if query.lower() in ['exit', 'quit', 'q']:
                print("\nExiting...")
                break

            print("\nProcessing...")
            output = run_intelligence_query(query)
            print_output(output)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            print(f"\nError: {str(e)}")


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                 MARKET INTELLIGENCE SYSTEM                           ║
║             Hackathon MVP - Agent-Based Intelligence                 ║
╚══════════════════════════════════════════════════════════════════════╝

Features:
  • RAG Agent: Semantic search across PDF documents
  • Financial Agent: 10+ financial metrics calculation
  • Alert Agent: Threshold-based alerts and risk detection
  • Supervisor Agent: Orchestration and synthesis
  • LangGraph Workflow: State management and flow control

Models: GLM 4.5/4.7 via OpenRouter
Database: MilvusDB (pdf_text_chunks, pdf_table_chunks)
    """)

    import argparse

    parser = argparse.ArgumentParser(description="Market Intelligence Query System")
    parser.add_argument("--examples", action="store_true", help="Run example queries")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--query", type=str, help="Single query")

    args = parser.parse_args()

    try:
        if args.examples:
            example_queries()
        elif args.interactive:
            interactive_mode()
        elif args.query:
            print_separator("QUERY")
            print(f"\n{args.query}\n")
            print("Processing...")
            output = run_intelligence_query(args.query)
            print_output(output)
        else:
            # Default: interactive mode
            interactive_mode()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
