/**
 * Dependency-free checks for the existing rate limit behavior.
 */
public final class RateLimitCheck {
    /**
     * Runs the current component checks.
     *
     * @param arguments unused command-line arguments
     */
    public static void main(String[] arguments) {
        if (new RateLimit(5).getUnits() != 5) {
            throw new AssertionError("The configured limit must be retained");
        }
        if (new RateLimit(0).getUnits() != 0) {
            throw new AssertionError("A zero limit is valid");
        }
    }
}
