package example;

import org.mapstruct.Mapper;

/**
 * In-memory user projection using MapStruct.
 */
@Mapper
public interface UserMapper {
    /**
     * Maps a user input to its display label.
     *
     * @param input source user data
     * @return the corresponding display label
     */
    UserLabel toLabel(UserInput input);

    /**
     * Source user value.
     *
     * @param name user display name
     */
    record UserInput(String name) {
    }

    /**
     * Output user label.
     *
     * @param name user display name
     */
    record UserLabel(String name) {
    }
}
