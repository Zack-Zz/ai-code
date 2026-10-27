package example;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import java.util.ArrayList;
import java.util.List;

/**
 * Persisted order with associated lines.
 */
@Entity
public class OrderEntity {
    /**
     * Persistent order identifier.
     */
    @Id
    private Long id;

    /**
     * Associated lines whose merge operations currently propagate from the order.
     */
    @OneToMany(fetch = FetchType.LAZY, cascade = CascadeType.MERGE)
    private List<OrderLine> lines = new ArrayList<>();

    /**
     * Creates an entity instance for the persistence provider.
     */
    protected OrderEntity() {
    }

    /**
     * Returns the associated line collection.
     *
     * @return associated lines, potentially loaded by the persistence provider
     */
    public List<OrderLine> getLines() {
        return lines;
    }
}
