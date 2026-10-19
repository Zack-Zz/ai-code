/**
 * Provides the discount shown by web ordering.
 */
public final class WebOrders {
    /**
     * Prevents construction of this stateless entry point.
     */
    private WebOrders() {
    }

    /**
     * Calculates the loyalty discount shared with phone ordering.
     *
     * @param subtotalCents order subtotal in cents
     * @param loyaltyMember whether the customer is a loyalty member
     * @return discount in cents
     * @throws IllegalArgumentException if the subtotal is negative
     */
    public static long discountCents(long subtotalCents, boolean loyaltyMember) {
        if (subtotalCents < 0) {
            throw new IllegalArgumentException("subtotal must be nonnegative");
        }
        return loyaltyMember && subtotalCents >= 10000L ? 500L : 0L;
    }
}
