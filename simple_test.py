import sys
sys.path.append('.')

# Test the Kelly Criterion calculation directly

def test_kelly_calculation():
    # Parameters
    edge_cents = 7  # Minimum edge
    probability = 0.7  # Minimum certainty
    MAX_RISK_PER_TRADE = 0.05  # 5% max risk
    portfolio_balance = 100000  # $1000 in cents
    
    print(f"Testing with edge: {edge_cents} cents, probability: {probability}")
    print(f"Portfolio balance: ${portfolio_balance / 100:.2f}")
    
    # Check edge threshold
    MINIMUM_EDGE_CENTS = 7
    if edge_cents < MINIMUM_EDGE_CENTS:
        print(f"Edge {edge_cents} < minimum {MINIMUM_EDGE_CENTS}, position size would be 0")
        return 0
    
    # Kelly calculation
    odds = 1.0
    kelly_fraction = (odds * probability - (1 - probability)) / odds
    print(f"Kelly fraction before limits: {kelly_fraction:.4f}")
    
    # Apply risk limits
    kelly_fraction = max(0, min(kelly_fraction, MAX_RISK_PER_TRADE))
    print(f"Kelly fraction after limits: {kelly_fraction:.4f}")
    
    # Calculate position size
    position_value = portfolio_balance * kelly_fraction
    print(f"Position value: ${position_value / 100:.2f}")
    
    position_size = int(position_value / 100)  # Convert cents to dollars
    print(f"Position size: {position_size} contracts")
    
    return position_size

if __name__ == "__main__":
    result = test_kelly_calculation()
    print(f"\nFinal result: {result} contracts")
