import java.util.Objects;
import java.util.OptionalLong;

/**
 * Reads purchase totals before a customer confirms checkout.
 */
public final class PreviewService {
    /**
     * Shared inventory used by previews and confirmed purchases.
     */
    private final Inventory inventory;

    /**
     * Creates a purchase preview service.
     * @param inventory inventory to inspect
     */
    public PreviewService(Inventory inventory) {
        this.inventory = Objects.requireNonNull(inventory);
    }

    /**
     * Previews an available purchase without reserving stock.
     * @param tenant current tenant
     * @param sku requested item key
     * @param units positive number of units
     * @return total in cents, or empty when the item or sufficient stock is unavailable
     * @throws IllegalArgumentException when units are nonpositive
     */
    public OptionalLong preview(String tenant, String sku, int units) {
        throw new UnsupportedOperationException("Preview is not implemented");
    }
}
