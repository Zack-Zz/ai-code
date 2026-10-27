/**
 * Dependency-free quota checks.
 */
public final class QuotaCheck {
    /**
     * Checks the existing typical capacity example.
     *
     * @param arguments unused command-line arguments
     */
    public static void main(String[] arguments) {
        if (new Quota(10).getCapacity() != 10) {
            throw new AssertionError("The quota must retain its capacity");
        }
    }
}
