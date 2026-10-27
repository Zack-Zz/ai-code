/**
 * Owns the delivery-fee policy used throughout checkout.
 */
public final class DeliveryFees {
    /**
     * Prevents construction of this stateless policy.
     */
    private DeliveryFees() {
    }

    /**
     * Quotes delivery for a nonnegative order subtotal.
     *
     * @param subtotalCents order subtotal in cents
     * @return delivery fee in cents
     * @throws IllegalArgumentException if the subtotal is negative
     */
    public static long quote(long subtotalCents) {
        if (subtotalCents < 0) {
            throw new IllegalArgumentException("subtotal must be nonnegative");
        }
        return subtotalCents < 5000L ? 800L : 0L;
    }
}
