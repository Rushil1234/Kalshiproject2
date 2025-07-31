import sys
sys.path.append('.')

from src.trading.trader import TradeExecutor
from config import MINIMUM_EDGE_CENTS, MAX_RISK_PER_TRADE

# Mock the constants that are imported
import config
config.MINIMUM_EDGE_CENTS = MINIMUM_EDGE_CENTS
config.MAX_RISK_PER_TRADE = MAX_RISK_PER_TRADE

def test_position_sizing():
    """Test the position sizing logic with different parameters"""
    # Create a mock client and trade executor
    class MockClient:
        def get_balance(self):
            return {'balance': 100000}  # $1000 in cents
    
    client = MockClient()
    executor = TradeExecutor(client)
    
    # Set the portfolio balance directly
    executor.portfolio_balance = 100000
    
    print(f"Current portfolio balance: ${executor.portfolio_balance / 100:.2f}")
    print(f"Current minimum edge: {MINIMUM_EDGE_CENTS} cents")
    print(f"Current max risk per trade: {MAX_RISK_PER_TRADE * 100}%")
    
    # Test different scenarios
    test_cases = [
        {"edge": 5, "probability": 0.6, "description": "Low edge, moderate probability"},
        {"edge": 7, "probability": 0.7, "description": "Current threshold values"},
        {"edge": 10, "probability": 0.8, "description": "Higher edge, high probability"},
        {"edge": 3, "probability": 0.55, "description": "Very low edge, low confidence"},
        {"edge": 1, "probability": 0.51, "description": "Minimal edge, minimal confidence"},
    ]
    
    for case in test_cases:
        print(f"\nTesting {case['description']}:")
        print(f"  Edge: {case['edge']} cents, Probability: {case['probability']:.2f}")
        
        # Calculate position size
        position_size = executor.calculate_position_size(case["edge"], case["probability"])
        print(f"  Position size: {position_size} contracts")
        
        # Debug the calculation steps
        if case["edge"] < MINIMUM_EDGE_CENTS:
            print(f"  -> Edge {case['edge']} < minimum {MINIMUM_EDGE_CENTS}, so position size is 0")
        else:
            edge_probability = case["edge"] / 100.0
            odds = 1.0
            kelly_fraction = (odds * case["probability"] - (1 - case["probability"])) / odds
            print(f"  -> Kelly fraction before limits: {kelly_fraction:.4f}")
            kelly_fraction = max(0, min(kelly_fraction, MAX_RISK_PER_TRADE))
            print(f"  -> Kelly fraction after limits: {kelly_fraction:.4f}")
            position_value = executor.portfolio_balance * kelly_fraction
            print(f"  -> Position value: ${position_value / 100:.2f}")
            position_size_calc = int(position_value / 100)
            print(f"  -> Position size calculated: {position_size_calc}")

if __name__ == "__main__":
    test_position_sizing()
