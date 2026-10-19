/**
 * Represents an independently deployed client compiled against the original API.
 */
public final class LegacyShipmentCaller {
    /**
     * Prevents construction of the evaluator entry point.
     */
    private LegacyShipmentCaller() {
    }

    /**
     * Calls original method and nested constructor descriptors without source recompilation.
     * @param args unused command-line arguments
     */
    public static void main(String[] args) {
        ShipmentService service = new ShipmentService();
        ShipmentService.Quote quote = service.quote(2);
        require(quote.feeCents() == 1600L, "legacy quote fee");
        ShipmentService.Quote constructed = new ShipmentService.Quote(23L, 4);
        require(constructed.feeCents() == 23L && constructed.estimatedDays() == 4,
                "legacy nested constructor and accessors");
        require(quote.getClass().isRecord(), "public quote must retain its record contract");
        require("ShipmentService$Quote".equals(quote.getClass().getName()), "legacy binary type name");
        System.out.println("Frozen legacy caller passed");
    }

    /**
     * Reports a failed deployed-client contract.
     * @param condition expected condition
     * @param message failure context
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
