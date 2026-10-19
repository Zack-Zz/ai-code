/**
 * Calculates the dispatch fee for application business operations.
 */
public final class DispatchService {
    /**
     * Creates a dispatch service using the current fixed fee policy.
     */
    public DispatchService() {
    }

    /**
     * Calculates a fee for a bounded parcel count and distance.
     *
     * @param parcelCount number of parcels from 1 through 100
     * @param distanceKm delivery distance from 1 through 1,000 km
     * @return dispatch fee in cents
     * @throws IllegalArgumentException if either input is outside its range
     */
    public long feeCents(int parcelCount, int distanceKm) {
        if (parcelCount < 1 || parcelCount > 100 || distanceKm < 1 || distanceKm > 1_000) {
            throw new IllegalArgumentException("parcel count or distance is outside its range");
        }
        return 200L * parcelCount + 10L * distanceKm;
    }
}
