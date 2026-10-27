/**
 * Provides quotations to independently deployed shipment clients.
 */
public final class ShipmentService {
    /**
     * Creates a stateless shipment service.
     */
    public ShipmentService() {
    }

    /**
     * Immutable public quotation returned to existing clients.
     * @param feeCents total shipment fee in cents
     * @param estimatedDays expected delivery time in days
     */
    public record Quote(long feeCents, int estimatedDays) {
    }

    /**
     * Calculates the quotation for a shipment.
     * @param parcelCount number of parcels, from one through one hundred
     * @return shipment quotation with a fee and expected delivery time
     * @throws IllegalArgumentException when the parcel count is outside its supported range
     */
    public Quote quote(int parcelCount) {
        if (parcelCount < 1 || parcelCount > 100) {
            throw new IllegalArgumentException("Parcel count out of range");
        }
        return new Quote(parcelCount * 800L, 0);
    }
}
