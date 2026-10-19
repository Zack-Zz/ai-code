/**
 * Decides eligibility under the settlement-owned withdrawal contract.
 */
public final class RefundWithdrawal {
    /**
     * Prevents construction of this stateless policy.
     */
    private RefundWithdrawal() {
    }

    /**
     * Checks whether a refund can still be withdrawn.
     *
     * @param status current refund status
     * @param elapsedMinutes minutes since refund creation
     * @return whether withdrawal is permitted
     * @throws IllegalArgumentException if status is null or elapsed time is negative
     */
    public static boolean canWithdraw(String status, long elapsedMinutes) {
        return "PENDING".equals(status) && elapsedMinutes <= 30L;
    }
}
