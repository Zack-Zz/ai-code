# Purchase preview

This Java 17 application has one inventory item: tenant `north`, SKU `pen`,
unit price 500 cents and three available units. Comments use English.

`CheckoutService.checkout` confirms a purchase: it reserves units and rejects an
unavailable item or insufficient stock with `IllegalStateException`. Existing
checkout callers depend on this command contract. `Inventory` exposes read-only
price/availability accessors and a reservation count for the existing application.

Complete `PreviewService.preview` to return the total in `OptionalLong` when the
tenant owns the item and sufficient units are available. Return empty for an
unknown/foreign item or insufficient stock. Reject nonpositive units with
`IllegalArgumentException`. A preview is read-only and repeated previews must not
affect future previews or checkouts. Preserve existing checkout behavior.

Only `src/PreviewService.java` may change. Existing source and this README are
application context, not evaluator-owned tests. No dependencies are required.
