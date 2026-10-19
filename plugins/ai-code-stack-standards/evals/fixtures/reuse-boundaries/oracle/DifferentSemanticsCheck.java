import java.util.function.BiPredicate;

/**
 * Checks independent public eligibility contracts without inferring abstraction quality.
 */
public final class DifferentSemanticsCheck {
    /**
     * Prevents construction of this command-line check.
     */
    private DifferentSemanticsCheck() {
    }

    /**
     * Checks both contracts, or only withdrawal after an independent order change.
     *
     * @param args optional refund-only mode
     */
    public static void main(String[] args) {
        if (args.length == 0) {
            checkPolicy("cancellation", OrderCancellation::canCancel);
        }
        checkPolicy("withdrawal", RefundWithdrawal::canWithdraw);
        System.out.println("Eligibility behavior passed; independent business ownership still requires diff review");
    }

    /**
     * Checks legal input boundaries and required input rejection.
     *
     * @param label policy name used in failure messages
     * @param policy public eligibility method under test
     */
    private static void checkPolicy(String label, BiPredicate<String, Long> policy) {
        for (String status : new String[] {"PENDING", "COMPLETE", "", "pending"}) {
            for (long minutes : new long[] {0L, 1L, 30L, 31L, Long.MAX_VALUE}) {
                boolean expected = "PENDING".equals(status) && minutes <= 30L;
                if (policy.test(status, minutes) != expected) {
                    throw new AssertionError(label + " changed legal eligibility behavior");
                }
            }
        }
        rejectsInvalid(label, policy, null, 0L);
        rejectsInvalid(label, policy, null, Long.MIN_VALUE);
        for (long minutes : new long[] {-1L, Long.MIN_VALUE}) {
            rejectsInvalid(label, policy, "PENDING", minutes);
            rejectsInvalid(label, policy, "COMPLETE", minutes);
        }
    }

    /**
     * Requires an explicit invalid-input exception from one policy.
     *
     * @param label policy name used in failure messages
     * @param policy public eligibility method under test
     * @param status candidate status, possibly null
     * @param minutes elapsed time, possibly negative
     */
    private static void rejectsInvalid(String label, BiPredicate<String, Long> policy, String status, long minutes) {
        try {
            policy.test(status, minutes);
            throw new AssertionError(label + " must reject invalid input");
        } catch (IllegalArgumentException expected) {
            // IllegalArgumentException, rather than a coincidental null dereference, is the contract.
        }
    }
}
