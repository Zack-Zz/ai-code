package example;

/**
 * A plain Java text helper with no persistence dependency.
 */
public final class TextKey {
    /**
     * Removes surrounding whitespace from a text key.
     *
     * @param value nonnull input text
     * @return the trimmed text
     */
    public String normalize(String value) {
        return value.strip();
    }
}
