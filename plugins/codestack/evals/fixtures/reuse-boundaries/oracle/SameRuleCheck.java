/**
 * Checks the shared discount contract without judging implementation structure.
 */
public final class SameRuleCheck {
    /**
     * Prevents construction of this command-line check.
     */
    private SameRuleCheck() {
    }

    /**
     * Checks both public entry points and an optional evaluator-selected change.
     *
     * @param args expected discount in cents
     */
    public static void main(String[] args) {
        long discount = args.length == 0 ? 700L : Long.parseLong(args[0]);
        for (long subtotal : new long[] {0L, 1L, 9999L, 10000L, 14999L, 15000L, 15001L, Long.MAX_VALUE}) {
            for (boolean member : new boolean[] {false, true}) {
                long expected = member && subtotal >= 15000L ? discount : 0L;
                if (WebOrders.discountCents(subtotal, member) != expected
                        || PhoneOrders.discountCents(subtotal, member) != expected) {
                    throw new AssertionError("Both entry points must apply the active loyalty discount: " + subtotal);
                }
            }
        }
        for (long subtotal : new long[] {-1L, Long.MIN_VALUE}) {
            for (boolean member : new boolean[] {false, true}) {
                rejectsNegative(subtotal, member);
            }
        }
        System.out.println("Discount behavior passed; shared ownership and abstraction still require diff review");
    }

    /**
     * Requires both public entry points to reject negative amounts.
     *
     * @param subtotal negative subtotal in cents
     * @param member whether the customer is a loyalty member
     */
    private static void rejectsNegative(long subtotal, boolean member) {
        try {
            WebOrders.discountCents(subtotal, member);
            throw new AssertionError("Web ordering must reject a negative subtotal");
        } catch (IllegalArgumentException expected) {
            // Invalid orders remain invalid at both entry points.
        }
        try {
            PhoneOrders.discountCents(subtotal, member);
            throw new AssertionError("Phone ordering must reject a negative subtotal");
        } catch (IllegalArgumentException expected) {
            // Invalid orders remain invalid at both entry points.
        }
    }
}
