import java.util.Objects;

/**
 * Confirms purchases and reserves inventory.
 */
public final class CheckoutService {
    /**
     * Inventory mutated by confirmed purchases.
     */
    private final Inventory inventory;

    /**
     * Creates a checkout command service.
     * @param inventory inventory used by confirmed purchases
     */
    public CheckoutService(Inventory inventory) {
        this.inventory = Objects.requireNonNull(inventory);
    }

    /**
     * Reserves the purchase and returns its total.
     * @param tenant current tenant
     * @param sku requested item key
     * @param units positive number of units
     * @return confirmed purchase total in cents
     * @throws IllegalArgumentException when units are nonpositive
     * @throws IllegalStateException when the owned item or enough stock is unavailable
     */
    public long checkout(String tenant, String sku, int units) {
        inventory.reserve(tenant, sku, units);
        return inventory.unitPrice(tenant, sku).orElseThrow() * units;
    }
}
