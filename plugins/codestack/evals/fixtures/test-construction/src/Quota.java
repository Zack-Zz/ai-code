/**
 * A strictly positive capacity quota.
 */
public final class Quota {
    /**
     * Maximum capacity, greater than zero.
     */
    private final int capacity;

    /**
     * Creates a quota with the requested capacity.
     *
     * @param capacity maximum capacity, greater than zero
     * @throws IllegalArgumentException when capacity is not positive
     */
    public Quota(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be positive");
        }
        this.capacity = capacity;
    }

    /**
     * Returns the allowed capacity.
     *
     * @return a positive capacity
     */
    public int getCapacity() {
        return capacity;
    }
}
