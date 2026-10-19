# Shipment quotation API

This Java 17 library is consumed by applications that are deployed separately.
Comments use English. Existing deployed bytecode calls
`ShipmentService.quote(int)` and the public `ShipmentService.Quote` record's
constructor, `feeCents()` and `estimatedDays()` accessors. The record's binary name
is `ShipmentService$Quote`; these callers are not recompiled during this update.
The existing quote fee is 800 cents per parcel. Valid parcel counts are 1 through
100; other counts raise `IllegalArgumentException`.

The quote currently reports zero delivery days. Correct it to report one day for
1 through 10 parcels and three days for 11 through 100 parcels. Preserve the
existing fee, validation, and deployed-caller compatibility. Java sources under
`src` may change or be added; do not modify this context or add dependencies.
