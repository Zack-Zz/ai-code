/**
 * Checks checkout results against the original and changed delivery policy.
 */
public final class ExistingImplementationCheck {
    /**
     * Prevents construction of this command-line check.
     */
    private ExistingImplementationCheck() {
    }

    /**
     * Checks public behavior using evaluator-owned expected results.
     *
     * @param args optional changed-policy mode
     */
    public static void main(String[] args) {
        boolean changed = args.length == 1 && "changed".equals(args[0]);
        for (long subtotal : new long[] {0L, 1L, 4999L, 5000L, 8999L, 9000L, Long.MAX_VALUE}) {
            long expected = changed ? (subtotal < 9000L ? 317L : 29L) : (subtotal < 5000L ? 800L : 0L);
            try {
                if (Checkout.previewFee(subtotal) != expected || Checkout.confirmedFee(subtotal) != expected) {
                    throw new AssertionError("Both checkout paths must follow the active delivery policy: " + subtotal);
                }
            } catch (UnsupportedOperationException unfinished) {
                throw new AssertionError("Confirmed checkout must return a fee", unfinished);
            }
        }
        for (long subtotal : new long[] {-1L, Long.MIN_VALUE}) {
            rejectsNegative(subtotal);
        }
        System.out.println("Checkout behavior passed for " + (changed ? "changed" : "original") + " policy");
    }

    /**
     * Requires the confirmed entry point to retain policy input validation.
     *
     * @param subtotal negative order subtotal
     */
    private static void rejectsNegative(long subtotal) {
        try {
            Checkout.confirmedFee(subtotal);
            throw new AssertionError("Confirmed checkout must reject a negative subtotal");
        } catch (IllegalArgumentException expected) {
            // A negative subtotal is outside the public policy contract.
        }
    }
}
