import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Set;

/**
 * Checks iterator behavior and public scope without prescribing private structure.
 */
public final class IteratorCheck {
    /**
     * Prevents construction of this executable check.
     */
    private IteratorCheck() {
    }

    /**
     * Executes the frozen snapshot and independent-iterator contracts.
     *
     * @param args unused command-line arguments
     */
    public static void main(String[] args) {
        for (String[] values : new String[][] {{}, {"one"}, {"same", "same", "last"},
                {"a", "b", "c", "d", "e"}}) {
            MessageWindow window = new MessageWindow(values);
            require(window.size() == values.length, "Snapshot size changed");
            Iterator<String> iterator = window.iterator();
            List<String> observed = new ArrayList<>();
            while (iterator.hasNext()) {
                require(iterator.hasNext(), "Repeated hasNext changed the cursor");
                observed.add(iterator.next());
            }
            require(observed.equals(List.of(values)), "hasNext traversal omitted or reordered messages");
            require(!iterator.hasNext(), "Exhausted iterator still reports an item");
            expectExhausted(iterator);
            expectExhausted(iterator);
            Iterator<String> direct = window.iterator();
            for (String value : values) {
                require(value.equals(readNext(direct)), "next requires an unnecessary hasNext call");
            }
            expectExhausted(direct);
            expectReadOnly(window.iterator());
        }

        String[] input = {"first", "second", "third"};
        MessageWindow snapshot = new MessageWindow(input);
        input[0] = "changed by caller";
        Iterator<String> left = snapshot.iterator();
        Iterator<String> right = snapshot.iterator();
        require("first".equals(left.next()), "Caller array mutation leaked into the snapshot");
        require("second".equals(left.next()), "Left iterator lost its own cursor position");
        require("first".equals(right.next()), "Iterators share advancement state");
        require("third".equals(left.next()), "Left iterator failed to return its last message");
        require("second".equals(right.next()), "Right iterator was advanced by the left iterator");
        require("third".equals(right.next()), "Right iterator failed to return its last message");
        expectExhausted(left);
        expectExhausted(right);
        expectNullRejected(null);
        expectNullRejected(new String[] {"valid", null});
        checkPublicApi();
        System.out.println("Iterator boundaries, snapshots, independent cursors and public API passed");
    }

    /**
     * Makes a fresh iterator's unexpected exhaustion a specific semantic failure.
     *
     * @param iterator fresh iterator expected to contain another message
     * @return the next message
     * @throws AssertionError if another iterator consumed this iterator's progress
     */
    private static String readNext(Iterator<String> iterator) {
        try {
            return iterator.next();
        } catch (NoSuchElementException exhausted) {
            throw new AssertionError("A fresh iterator did not provide independent traversal", exhausted);
        }
    }

    /**
     * Checks exhaustion using the JDK exception contract.
     *
     * @param iterator exhausted iterator
     * @throws AssertionError if next returns a value instead of rejecting exhaustion
     */
    private static void expectExhausted(Iterator<String> iterator) {
        try {
            iterator.next();
        } catch (NoSuchElementException expected) {
            return;
        }
        throw new AssertionError("Exhausted iterator did not throw NoSuchElementException");
    }

    /**
     * Checks that neither a fresh nor an advanced cursor supports removal.
     *
     * @param iterator iterator whose removal contract is read-only
     * @throws AssertionError if removal succeeds or uses a different exception
     */
    private static void expectReadOnly(Iterator<String> iterator) {
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                iterator.remove();
                throw new AssertionError("Iterator allowed removal");
            } catch (UnsupportedOperationException expected) {
                // The read-only contract applies before and after advancement.
            }
            if (iterator.hasNext()) {
                iterator.next();
            }
        }
    }

    /**
     * Checks the existing constructor's null rejection contract.
     *
     * @param values null array or array containing null
     * @throws AssertionError if construction accepts null input
     */
    private static void expectNullRejected(String[] values) {
        try {
            new MessageWindow(values);
        } catch (NullPointerException expected) {
            return;
        }
        throw new AssertionError("Snapshot constructor accepted null input");
    }

    /**
     * Rejects scope expansion while allowing any equivalent private implementation.
     *
     * @throws AssertionError if a new public member or helper type is introduced
     */
    private static void checkPublicApi() {
        for (var method : MessageWindow.class.getDeclaredMethods()) {
            if (Modifier.isPublic(method.getModifiers()) && !method.isSynthetic()) {
                require(Set.of("size", "iterator").contains(method.getName())
                                && method.getParameterCount() == 0,
                        "The fix added an unrelated public method");
            }
        }
        for (var field : MessageWindow.class.getDeclaredFields()) {
            require(!Modifier.isPublic(field.getModifiers()), "The fix exposed snapshot state");
        }
        for (var type : MessageWindow.class.getDeclaredClasses()) {
            require(!Modifier.isPublic(type.getModifiers()), "The fix added a public helper type");
        }
        var constructors = MessageWindow.class.getConstructors();
        require(constructors.length == 1
                        && List.of(constructors[0].getParameterTypes()).equals(List.of(String[].class)),
                "The fix added an unrelated public constructor");
    }

    /**
     * Rejects a semantic failure using a stable explanatory message.
     *
     * @param condition expected contract condition
     * @param message assertion failure description
     * @throws AssertionError if the condition is false
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
