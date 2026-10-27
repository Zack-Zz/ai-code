package example;

import java.util.List;
import java.util.Map;
import java.util.Set;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * Tenant-scoped user queries backed by a MyBatis XML mapping.
 */
@Mapper
public interface UserMapper {
    /**
     * Loads the selected users in one bounded lookup.
     *
     * @param tenantId trusted tenant identifier
     * @param userIds validated nonempty set within the request size limit
     * @return matching user rows, or an empty list when none exist
     */
    List<Map<String, Object>> findByIds(
            @Param("tenantId") long tenantId, @Param("userIds") Set<Long> userIds);
}
