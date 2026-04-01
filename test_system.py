"""
Complete system test for Stardew Valley AI Research Assistant
Tests the entire Deep Research flow end-to-end
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.deep_research_flow import DeepResearchFlow
from app.autogen_config import get_llm_config

async def test_deep_research_flow():
    """Test the complete Deep Research flow"""

    print("\n" + "="*80)
    print("START: Deep Research Flow System Test")
    print("="*80 + "\n")

    # Test configuration
    test_question = "星露谷物语中，第一年春季最赚钱的农作物是什么？"
    model = "qwen"

    print(f"📋 Test Configuration:")
    print(f"   Question: {test_question}")
    print(f"   Model: {model}")
    print(f"   LLM Config: {get_llm_config(model)}\n")

    # Initialize DeepResearchFlow
    print("🔧 Initializing DeepResearchFlow...")
    flow = DeepResearchFlow(model=model)
    print(f"   ✅ Flow initialized with session_id: {flow.session_id}\n")

    try:
        # Execute the research flow
        print("🚀 Executing Deep Research Flow (5 steps):\n")
        result = await flow.execute(test_question)

        # Display results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80 + "\n")

        print(f"✅ Research completed successfully\n")
        print(f"📊 Summary:")
        print(f"   Question Type: {result.get('question_type', 'N/A')}")
        print(f"   Subtasks Count: {result.get('subtasks_count', 0)}")
        print(f"   Evidence Count: {result.get('evidence_count', 0)}")
        print(f"   Evidence Quality: {result.get('evidence_quality', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        print(f"   Final Answer Preview: {result.get('final_answer', 'N/A')[:200]}...\n")

        # Show research flow stages
        print("🔄 Research Flow Stages:")
        research_flow = result.get('research_flow', [])
        for i, stage in enumerate(research_flow, 1):
            stage_name = stage.get('stage', 'unknown')
            timestamp = stage.get('timestamp', 'N/A')
            print(f"   {i}. {stage_name.upper()}: {timestamp}")

        # Show sources
        sources = result.get('sources', [])
        if sources:
            print(f"\n📚 Sources ({len(sources)} total):")
            for i, source in enumerate(sources[:5], 1):
                print(f"   {i}. {source[:80]}...")

        print("\n" + "="*80)
        print("TEST PASSED ✅")
        print("="*80 + "\n")

        return True

    except Exception as e:
        print("\n" + "="*80)
        print("TEST FAILED ❌")
        print("="*80 + "\n")
        print(f"Error: {str(e)}")
        print(f"Error Type: {type(e).__name__}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_config():
    """Test LLM configuration"""
    print("\n" + "="*80)
    print("LLM Configuration Test")
    print("="*80 + "\n")

    configs = ["qwen", "gpt4", "claude"]

    for config_name in configs:
        try:
            config = get_llm_config(config_name)
            api_key = config.get('api_key', '')
            has_key = bool(api_key and api_key != '')
            status = "✅ Configured" if has_key else "⚠️ Missing API Key"

            print(f"{config_name.upper()}: {status}")
            print(f"   Model: {config.get('model', 'N/A')}")
            print(f"   Base URL: {config.get('base_url', 'N/A')}")
            print()
        except Exception as e:
            print(f"{config_name.upper()}: ❌ Error - {str(e)}\n")


async def main():
    """Main test runner"""

    # Test LLM configs first
    await test_llm_config()

    # Test the full flow
    success = await test_deep_research_flow()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
