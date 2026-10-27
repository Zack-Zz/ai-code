# Dispatch quotes

Java 17, with no external dependencies. `DispatchService` is an application-owned
business service: its instance is reused by callers. This fixture does not use
Spring annotations or execute a Spring container.

The existing fee policy accepts 1 through 100 parcels and a distance of 1 through
1,000 km. The fee in cents is `200 * parcelCount + 10 * distanceKm`. A structured
quote also needs an estimate of one day through 50 km, otherwise three days.
The existing `feeCents` method and its behavior remain public contracts.

Comments in this project use English.
