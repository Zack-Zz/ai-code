import java.util.OptionalLong;

/**
 * Checks preview results and the command contract without prescribing reuse choices.
 */
public final class PreviewCheck {
    /**
     * Prevents construction of the evaluator entry point.
     */
    private PreviewCheck() {
    }

    /**
     * Runs each contract category on an independent inventory instance.
     * @param args optional single contract category
     */
    public static void main(String[] args) {
        try {
            verify(args);
        } catch (RuntimeException failure) {
            throw new AssertionError("Preview operation violated requested contract", failure);
        }
        System.out.println("Preview contracts passed");
    }

    /**
     * Invokes the requested subset of preview contracts.
     * @param args optional single contract category
     */
    private static void verify(String[] args) {
        if (args.length == 0 || "side-effects".equals(args[0])) {
            sideEffects();
        }
        if (args.length == 0 || "unavailable".equals(args[0])) {
            unavailable();
        }
        if (args.length == 0 || "invalid".equals(args[0])) {
            invalid();
        }
        if (args.length == 0 || "checkout".equals(args[0])) {
            checkout();
        }
    }

    /**
     * Verifies repeated preview results and inventory preservation.
     */
    private static void sideEffects() {
        Inventory inventory = new Inventory();
        PreviewService preview = new PreviewService(inventory);
        total(preview.preview("north", "pen", 2), 1000L, "first preview");
        require(inventory.reservedUnits() == 0, "preview must not reserve inventory");
        total(preview.preview("north", "pen", 2), 1000L, "repeated preview");
        require(inventory.reservedUnits() == 0, "repeated preview must remain read-only");
        CheckoutService checkout = new CheckoutService(inventory);
        require(checkout.checkout("north", "pen", 1) == 500L, "checkout total");
        require(inventory.reservedUnits() == 1, "checkout must still reserve units");
        total(preview.preview("north", "pen", 2), 1000L, "remaining stock preview");
        require(preview.preview("north", "pen", 3).isEmpty(), "preview must use remaining stock");
        require(inventory.reservedUnits() == 1, "preview after checkout must remain read-only");
    }

    /**
     * Verifies absence semantics, tenant isolation and no side effects on rejected previews.
     */
    private static void unavailable() {
        Inventory inventory = new Inventory();
        PreviewService preview = new PreviewService(inventory);
        require(preview.preview("south", "pen", 1).isEmpty(), "foreign tenant must receive empty");
        require(preview.preview("north", "missing", 1).isEmpty(), "unknown SKU must receive empty");
        require(preview.preview("north", "pen", 4).isEmpty(), "insufficient stock must receive empty");
        require(preview.preview("north", "pen", Integer.MAX_VALUE).isEmpty(), "huge request must receive empty");
        require(inventory.reservedUnits() == 0, "unavailable previews must not reserve units");
    }

    /**
     * Verifies invalid-unit exceptions even when the item is unavailable.
     */
    private static void invalid() {
        Inventory inventory = new Inventory();
        PreviewService preview = new PreviewService(inventory);
        for (int units : new int[] {0, -1, Integer.MIN_VALUE}) {
            try {
                preview.preview("south", "missing", units);
                throw new AssertionError("nonpositive units must be rejected");
            } catch (IllegalArgumentException expected) {
                require(inventory.reservedUnits() == 0, "invalid preview must not reserve units");
            }
        }
    }

    /**
     * Verifies the unchanged checkout command still mutates and rejects unavailable stock.
     */
    private static void checkout() {
        Inventory inventory = new Inventory();
        CheckoutService checkout = new CheckoutService(inventory);
        require(checkout.checkout("north", "pen", 3) == 1500L, "checkout total for all stock");
        require(inventory.reservedUnits() == 3, "confirmed checkout must reserve all units");
        try {
            checkout.checkout("north", "pen", 1);
            throw new AssertionError("unavailable checkout must reject");
        } catch (IllegalStateException expected) {
            require(inventory.reservedUnits() == 3, "rejected checkout must preserve reservations");
        }
    }

    /**
     * Checks a present preview amount.
     * @param actual actual optional preview amount
     * @param expected expected total
     * @param context assertion context
     */
    private static void total(OptionalLong actual, long expected, String context) {
        require(actual.isPresent() && actual.getAsLong() == expected, context + " total");
    }

    /**
     * Reports a semantic assertion failure.
     * @param condition expected condition
     * @param message failure context
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
