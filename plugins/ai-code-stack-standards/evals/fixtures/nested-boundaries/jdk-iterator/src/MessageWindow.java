import java.util.Iterator;
import java.util.NoSuchElementException;
import java.util.Objects;

/**
 * Exposes a read-only snapshot of messages through independent JDK iterators.
 */
public final class MessageWindow implements Iterable<String> {
    /**
     * Holds the private copy read by each iterator.
     */
    private final String[] messages;

    /**
     * Creates a snapshot without retaining the caller's array.
     *
     * @param messages messages to expose in their original order
     * @throws NullPointerException if the array or any element is null
     */
    public MessageWindow(String... messages) {
        this.messages = Objects.requireNonNull(messages, "messages").clone();
        for (String message : this.messages) {
            Objects.requireNonNull(message, "message");
        }
    }

    /**
     * Returns the number of messages in the snapshot.
     *
     * @return snapshot size
     */
    public int size() {
        return messages.length;
    }

    /**
     * Creates an independent cursor over the private snapshot.
     *
     * @return a read-only iterator starting at the first message
     */
    @Override
    public Iterator<String> iterator() {
        return new Cursor();
    }

    /**
     * Holds iteration progress while reading the enclosing snapshot privately.
     */
    private final class Cursor implements Iterator<String> {
        /**
         * Identifies the next message for this iterator only.
         */
        private int nextIndex;

        /**
         * Creates a cursor at the start of the enclosing snapshot.
         */
        private Cursor() {
        }

        /**
         * Reports whether this cursor has a remaining message.
         *
         * @return whether another call to next can return a message
         */
        @Override
        public boolean hasNext() {
            return nextIndex < messages.length - 1;
        }

        /**
         * Returns the next message without changing other iterators.
         *
         * @return the next message in snapshot order
         * @throws NoSuchElementException if this cursor is exhausted
         */
        @Override
        public String next() {
            if (nextIndex >= messages.length) {
                throw new NoSuchElementException();
            }
            return messages[nextIndex++];
        }
    }
}
