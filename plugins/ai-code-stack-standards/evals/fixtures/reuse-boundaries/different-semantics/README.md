# Cancellation and withdrawal

This module uses English code documentation and Java 17, without dependencies.
Order cancellation is owned by order fulfillment; refund withdrawal is owned by
payment settlement. They happen to permit PENDING requests within 30 elapsed
minutes today. These are independent business contracts: inventory-reservation
changes may change cancellation without changing withdrawal, and bank-submission
changes may change withdrawal without changing cancellation. Both public methods
must remain available. Null status and negative elapsed time are invalid inputs.
