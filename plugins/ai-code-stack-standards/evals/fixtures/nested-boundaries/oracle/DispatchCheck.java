import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/**
 * Checks quote behavior without choosing a result type name or nesting shape.
 */
public final class DispatchCheck {
    /**
     * Prevents construction of this executable check.
     */
    private DispatchCheck() {
    }

    /**
     * Executes the frozen dispatch contracts against candidate production code.
     *
     * @param args unused command-line arguments
     * @throws ReflectiveOperationException if the requested public API is absent
     */
    public static void main(String[] args) throws ReflectiveOperationException {
        DispatchService service = new DispatchService();
        Method quote;
        try {
            quote = DispatchService.class.getMethod("quote", int.class, int.class);
        } catch (NoSuchMethodException missing) {
            throw new AssertionError("The requested public quote method is absent", missing);
        }
        for (int parcels : new int[] {1, 2, 100}) {
            for (int distance : new int[] {1, 49, 50, 51, 1_000}) {
                long expectedFee = 200L * parcels + 10L * distance;
                require(service.feeCents(parcels, distance) == expectedFee,
                        "Existing fee policy changed");
                Object result = quote.invoke(service, parcels, distance);
                require(result != null, "Quote result must not be null");
                Object fee = result.getClass().getMethod("feeCents").invoke(result);
                Object days = result.getClass().getMethod("estimatedDays").invoke(result);
                require(fee instanceof Number && ((Number) fee).doubleValue() == expectedFee,
                        "Quote fee does not preserve the existing policy");
                require(days instanceof Number
                                && ((Number) days).doubleValue() == (distance <= 50 ? 1 : 3),
                        "Estimated days violate the 50 km boundary");
            }
        }
        for (int[] invalid : new int[][] {{0, 1}, {101, 1}, {1, 0}, {1, 1_001},
                {Integer.MIN_VALUE, 1}, {1, Integer.MAX_VALUE}}) {
            expectRejected(service, quote, invalid[0], invalid[1]);
        }
        System.out.println("Dispatch quote fees, day boundary and input rejection passed");
    }

    /**
     * Checks rejection on both the existing and newly requested entry points.
     *
     * @param service candidate dispatch service
     * @param quote requested public quote method
     * @param parcels invalid parcel count or a valid companion value
     * @param distance invalid distance or a valid companion value
     * @throws ReflectiveOperationException if the candidate API cannot be invoked
     */
    private static void expectRejected(DispatchService service, Method quote,
            int parcels, int distance) throws ReflectiveOperationException {
        boolean originalRejected = false;
        try {
            service.feeCents(parcels, distance);
        } catch (IllegalArgumentException expected) {
            originalRejected = true;
        }
        require(originalRejected, "Existing fee method accepted an out-of-range input");
        try {
            quote.invoke(service, parcels, distance);
        } catch (InvocationTargetException failure) {
            require(failure.getCause() instanceof IllegalArgumentException,
                    "Quote rejected invalid input with an unexpected exception");
            return;
        }
        throw new AssertionError("Quote accepted an out-of-range input");
    }

    /**
     * Rejects a semantic failure using a stable explanatory message.
     *
     * @param condition expected contract condition
     * @param message assertion failure description
     * @throws AssertionError if the condition is false
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
