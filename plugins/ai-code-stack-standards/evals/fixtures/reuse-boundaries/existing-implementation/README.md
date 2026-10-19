# Checkout fees

This module uses English code documentation and Java 17, without dependencies.
`DeliveryFees.quote` owns the delivery-fee policy for all checkout entry points.
`Checkout.previewFee` already uses that policy. A confirmed checkout must use the
same live policy, including later policy changes. Negative subtotals are invalid.
