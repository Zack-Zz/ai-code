package example;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/**
 * Persisted order line used by the routing snapshot.
 */
@Entity
public class OrderLine {
    /**
     * Persistent line identifier.
     */
    @Id
    private Long id;

    /**
     * Creates an entity instance for the persistence provider.
     */
    protected OrderLine() {
    }
}
