/**
 * Decides eligibility under the fulfillment-owned cancellation contract.
 */
public final class OrderCancellation {
    /**
     * Prevents construction of this stateless policy.
     */
    private OrderCancellation() {
    }

    /**
     * Checks whether an order can still be cancelled.
     *
     * @param status current order status
     * @param elapsedMinutes minutes since order creation
     * @return whether cancellation is permitted
     * @throws IllegalArgumentException if status is null or elapsed time is negative
     */
    public static boolean canCancel(String status, long elapsedMinutes) {
        return "PENDING".equals(status) && elapsedMinutes <= 30L;
    }
}
