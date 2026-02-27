#!/bin/bash

# Usage: ./concurrent-test.sh pessimistic OR ./concurrent-test.sh optimistic
ENDPOINT=$1
PRODUCT_ID=1
QUANTITY=10
URL="http://localhost:8080/api/orders/$ENDPOINT"

if [ -z "$ENDPOINT" ]; then
  echo "Usage: $0 <pessimistic|optimistic>"
  exit 1
fi

# 1. Reset product stock to initial state
echo "Resetting product stock..."
curl -s -X POST http://localhost:8080/api/products/reset > /dev/null

echo -e "\nStarting concurrent test on: $URL"
echo "Sending 20 requests to buy $QUANTITY units each (Total demand: 200, Stock: 100)..."

# 2. Fire 20 concurrent requests
for i in {1..20}
do
  # Send request in background (&)
  curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"productId\": $PRODUCT_ID, \"quantity\": $QUANTITY, \"userId\": \"user_$i\"}" \
    $URL &
  
  # Slight stagger to ensure they hit the server nearly at the same time
  sleep 0.02
done

# Wait for all background processes to finish
wait

echo -e "\n\nTest finished. Fetching stats..."
# 3. Check the stats endpoint for the results
curl -s http://localhost:8080/api/orders/stats | python3 -m json.tool