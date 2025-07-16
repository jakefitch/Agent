#!/usr/bin/env python3
import json
import os
from ollama import OllamaClient

def load_structured_claims():
    """Load the structured claims JSON file from the same directory."""
    json_file = os.path.join(os.path.dirname(__file__), "structured_claims.json")
    
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found!")
        print("Please run gateway_eob_scraper.py first to generate the structured claims data.")
        return None
    
    try:
        with open(json_file, 'r') as f:
            claims_data = json.load(f)
        print(f"✅ Loaded {len(claims_data)} claims from {json_file}")
        return claims_data
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return None

def analyze_single_claim(client, claim_data, model_name, prompt):
    """Analyze a single claim using the specified AI model and prompt."""
    try:
        # Create focused prompt for single claim analysis
        full_prompt = f"""
You are an expert medical claims analyst. Analyze this single claim and determine if it was paid or denied.

{prompt}

Claim Data:
{json.dumps(claim_data, indent=2)}

Please provide a brief analysis focusing on:
1. Was this claim paid or denied?
2. If denied, what was the reason?
3. Key details about the claim (patient, amounts, etc.)
"""
        
        # Generate response using the generate method
        response = client.generate(full_prompt, model=model_name)
        
        return response
        
    except Exception as e:
        print(f"❌ Error analyzing claim {claim_data.get('claim_number', 'unknown')}: {e}")
        return None

def analyze_claims_chunked(claims_data, model_name, prompt):
    """Analyze claims one by one for faster processing."""
    client = OllamaClient()
    results = []
    
    print(f"🤖 Analyzing {len(claims_data)} claims individually with model: {model_name}")
    print(f"📝 Prompt: {prompt}")
    print("=" * 60)
    
    for i, claim in enumerate(claims_data, 1):
        print(f"⏳ Analyzing claim {i}/{len(claims_data)}...")
        
        result = analyze_single_claim(client, claim, model_name, prompt)
        
        if result:
            claim_result = {
                "claim_number": claim.get("claim_number", i),
                "analysis": result
            }
            results.append(claim_result)
            
            # Print brief summary
            print(f"✅ Claim {i}: Analysis complete")
        else:
            print(f"❌ Claim {i}: Analysis failed")
    
    return results

def main():
    print("🔍 EOB Claims Analyzer (Chunked Processing)")
    print("=" * 50)
    
    # Load claims data
    claims_data = load_structured_claims()
    if not claims_data:
        return
    
    selected_model = "llama3:8b"
    
    # Test the model connection
    client = OllamaClient()
    print("Models:")
    print("=" * 40)
    print(client.get_models())
    print("=" * 40)
    client.test_model_connection(selected_model)
    
    # Get analysis prompt
    print("\n💡 Enter your analysis prompt:")
    print("Examples:")
    print("- 'Look for claim denials and let me know what claims denied and why'")
    print("- 'Check if claims were paid in full or partially'")
    print("- 'Identify any claims with unusual payment amounts'")
    
    prompt = input("\nYour prompt: ").strip()
    
    if not prompt:
        print("❌ No prompt provided. Using default analysis.")
        prompt = "Look for claim denials and let me know what claims denied and why."
    
    # Run chunked analysis
    print("\n" + "=" * 50)
    results = analyze_claims_chunked(claims_data, selected_model, prompt)
    
    if results:
        print("\n📊 Analysis Results Summary:")
        print("=" * 50)
        
        # Print summary of results
        for result in results:
            print(f"\n🔍 Claim {result['claim_number']}:")
            print("-" * 30)
            print(result['analysis'])
            print("-" * 30)
        
        # Save detailed results
        output_file = os.path.join(os.path.dirname(__file__), "analysis_results.txt")
        with open(output_file, 'w') as f:
            f.write(f"Model: {selected_model}\n")
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Claims analyzed: {len(results)}\n")
            f.write("\n" + "=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"Claim {result['claim_number']}:\n")
                f.write("-" * 30 + "\n")
                f.write(result['analysis'])
                f.write("\n" + "-" * 30 + "\n\n")
        
        print(f"\n✅ Detailed results saved to: {output_file}")
    else:
        print("❌ Analysis failed. Please check your model and try again.")

if __name__ == "__main__":
    main()
