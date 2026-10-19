/**
 * Maximum units allowed for one request.
 */
public final class RateLimit {
    /**
     * Nonnegative maximum request size, measured in units.
     */
    private final int units;

    /**
     * Creates a request limit.
     *
     * @param units nonnegative maximum request size
     * @throws IllegalArgumentException when units is negative
     */
    public RateLimit(int units) {
        if (units < 0) {
            throw new IllegalArgumentException("Units must not be negative");
        }
        this.units = units;
    }

    /**
     * Returns the configured maximum request size.
     *
     * @return nonnegative maximum units per request
     */
    public int getUnits() {
        return units;
    }
}
