import java.util.Map;

/**
 * Delegates to an external storage client whose implementation is not supplied.
 */
public final class StoreLookup {
    /**
     * Client supplied by the application.
     */
    private final StoreClient client;

    /**
     * Creates a lookup using the supplied storage client.
     *
     * @param client application storage client
     */
    public StoreLookup(StoreClient client) {
        this.client = client;
    }

    /**
     * Reads one document by its external key.
     *
     * @param key document key
     * @return stored fields, or an empty map when absent
     */
    public Map<String, String> find(String key) {
        return client.read(key);
    }

    /**
     * Storage boundary without any declared SQL or ORM contract.
     */
    public interface StoreClient {
        /**
         * Reads stored fields for a key.
         *
         * @param key document key
         * @return stored fields, or an empty map when absent
         */
        Map<String, String> read(String key);
    }
}
