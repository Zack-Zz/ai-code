import java.lang.reflect.InvocationTargetException;

/**
 * Checks quotation semantics independently of the implementation's type location.
 */
public final class ShipmentCheck {
    /**
     * Prevents construction of the evaluator entry point.
     */
    private ShipmentCheck() {
    }

    /**
     * Checks fee, delivery boundaries and validation through the public operation.
     * @param args unused command-line arguments
     * @throws ReflectiveOperationException when the requested public API is unavailable
     */
    public static void main(String[] args) throws ReflectiveOperationException {
        ShipmentService service = new ShipmentService();
        for (int count : new int[] {1, 2, 9, 10, 11, 12, 99, 100}) {
            Object quote = ShipmentService.class.getMethod("quote", int.class).invoke(service, count);
            long fee = ((Number) quote.getClass().getMethod("feeCents").invoke(quote)).longValue();
            int days = ((Number) quote.getClass().getMethod("estimatedDays").invoke(quote)).intValue();
            require(fee == count * 800L, "quotation fee for " + count);
            require(days == (count <= 10 ? 1 : 3), "delivery days for " + count);
        }
        for (int count : new int[] {Integer.MIN_VALUE, -1, 0, 101, Integer.MAX_VALUE}) {
            try {
                ShipmentService.class.getMethod("quote", int.class).invoke(service, count);
                throw new AssertionError("out-of-range parcel count must be rejected");
            } catch (InvocationTargetException failure) {
                require(failure.getCause() instanceof IllegalArgumentException,
                        "out-of-range exception type");
            }
        }
        System.out.println("Shipment quotation semantics passed");
    }

    /**
     * Reports a failed quotation assertion.
     * @param condition expected condition
     * @param message failure context
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
