import java.util.OptionalLong;

/**
 * Stores the application's single tenant-owned inventory item.
 */
public final class Inventory {
    /**
     * Units already reserved by confirmed purchases.
     */
    private int reservedUnits;

    /**
     * Creates inventory with three available pens.
     */
    public Inventory() {
    }

    /**
     * Reads the owned item's price without changing inventory.
     * @param tenant current tenant
     * @param sku requested item key
     * @return owned item's unit price, or empty for an unavailable item
     */
    public OptionalLong unitPrice(String tenant, String sku) {
        return "north".equals(tenant) && "pen".equals(sku)
                ? OptionalLong.of(500L) : OptionalLong.empty();
    }

    /**
     * Reads units available to the current tenant without changing inventory.
     * @param tenant current tenant
     * @param sku requested item key
     * @return remaining owned units, or zero for an unavailable item
     */
    public int availableUnits(String tenant, String sku) {
        return unitPrice(tenant, sku).isPresent() ? 3 - reservedUnits : 0;
    }

    /**
     * Reserves units for a confirmed purchase.
     * @param tenant current tenant
     * @param sku requested item key
     * @param units positive number of units
     * @throws IllegalArgumentException when units are nonpositive
     * @throws IllegalStateException when the owned item or enough stock is unavailable
     */
    public void reserve(String tenant, String sku, int units) {
        if (units <= 0) {
            throw new IllegalArgumentException("Units must be positive");
        }
        if (unitPrice(tenant, sku).isEmpty() || availableUnits(tenant, sku) < units) {
            throw new IllegalStateException("Inventory unavailable");
        }
        reservedUnits += units;
    }

    /**
     * Reads the number of units reserved by confirmed purchases.
     * @return confirmed reservation count
     */
    public int reservedUnits() {
        return reservedUnits;
    }
}
