/**
 * Exposes preview and confirmed delivery fees for checkout.
 */
public final class Checkout {
    /**
     * Prevents construction of these stateless entry points.
     */
    private Checkout() {
    }

    /**
     * Quotes delivery for the checkout preview.
     *
     * @param subtotalCents order subtotal in cents
     * @return delivery fee in cents
     * @throws IllegalArgumentException if the subtotal is negative
     */
    public static long previewFee(long subtotalCents) {
        return DeliveryFees.quote(subtotalCents);
    }

    /**
     * Quotes delivery for a confirmed checkout under the same policy.
     *
     * @param subtotalCents order subtotal in cents
     * @return delivery fee in cents
     * @throws IllegalArgumentException if the subtotal is negative
     */
    public static long confirmedFee(long subtotalCents) {
        throw new UnsupportedOperationException("confirmed quote is unfinished");
    }
}
