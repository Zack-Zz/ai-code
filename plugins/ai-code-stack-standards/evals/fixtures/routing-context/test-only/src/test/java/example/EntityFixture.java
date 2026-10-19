package example;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/**
 * A persistence mapping used only by test-source inspection scenarios.
 */
@Entity
public class EntityFixture {
    /**
     * Persistent identifier for the test mapping.
     */
    @Id
    private Long id;

    /**
     * Creates an instance for a persistence provider in a test environment.
     */
    protected EntityFixture() {
    }
}
