import sys
sys.path.append('.')

from clients import KalshiBaseClient, KalshiHttpClient

# Check if place_order method exists in both classes
def test_method_inheritance():
    print("Checking method inheritance...")
    
    # Check if place_order exists in KalshiBaseClient
    if hasattr(KalshiBaseClient, 'place_order'):
        print("KalshiBaseClient has place_order method")
    else:
        print("KalshiBaseClient does NOT have place_order method")
    
    # Check if place_order exists in KalshiHttpClient
    if hasattr(KalshiHttpClient, 'place_order'):
        print("KalshiHttpClient has place_order method (inherited)")
    else:
        print("KalshiHttpClient does NOT have place_order method")
        
    # List all methods in KalshiHttpClient
    print("\nMethods in KalshiHttpClient:")
    methods = [method for method in dir(KalshiHttpClient) if not method.startswith('_')]
    for method in methods:
        print(f"  {method}")

if __name__ == "__main__":
    test_method_inheritance()
