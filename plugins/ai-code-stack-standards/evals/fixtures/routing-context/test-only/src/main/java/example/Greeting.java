package example;

/**
 * A production helper that does not use the test-only persistence dependency.
 */
public final class Greeting {
    /**
     * Builds a greeting for a known display name.
     *
     * @param name nonnull display name
     * @return greeting text
     */
    public String forName(String name) {
        return "Hello, " + name;
    }
}
