package example;

/**
 * Customer whose persistence mapping is owned by XML metadata.
 */
public class Customer {
    /**
     * Customer identifier.
     */
    private Long id;

    /**
     * Customer label stored through the XML column mapping.
     */
    private String displayName;

    /**
     * Creates an instance for the persistence provider.
     */
    protected Customer() {
    }
}
