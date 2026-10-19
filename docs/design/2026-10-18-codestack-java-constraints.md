# CodeStack Java 编码规范设计稿

CodeStack · `ai-code-stack-standards` · 2026-10-18

状态：已按批准的插件结构实现英文执行规则，等待用户 Review。
当前新增规则及验证范围见 [复用、抽取与嵌套类型交付](../reviews/2026-10-18-codestack-reuse-and-nesting.md)，
上一轮记录见 [边界修复与行为复核](../reviews/2026-10-18-codestack-boundary-fixes.md)，
首轮记录保留在 [实现与验证报告](../reviews/2026-10-18-codestack-implementation.md)。
自动选择逻辑、资源布局和分步开发计划见[插件设计与开发计划](2026-10-18-codestack-plugin-design.md)。

本稿只保留用户明确的写法，以及需要防止智能体绕过或错误落实的具体要求。
不补写通用 Java 教程，不规定业务代码的缩进、换行、行宽和 import 排序。
规则用于本次新增、修改的代码，不触发无关文件整改。

插件中供智能体读取的 Skill、规则正文和最小示例仅维护英文；本设计稿保持中文。
执行规则采用英文，不代表目标项目的代码注释必须采用英文。本文示例使用中文便于评审，
实际注释仍遵循下面的语言选择顺序。

实现时，第 1—4 节（含 4.1—4.3）进入 `references/java.md`，第 5—7 节进入 `references/data-access.md`，
第 8 节进入 `references/jpa.md`，第 9 节进入 `references/mybatis.md`。
框架规则补充本框架的具体风险，共通要求只维护一份；实际读取范围由本次代码与调用链决定。
仅补充 Java 注释时，不因文件属于某 ORM 就自动读取数据访问和框架规则。
第 5—9 节首版面向已确认的关系型数据库 / SQL 访问；不能因为代码访问了未知存储，
就套用 IN、JOIN、SQL 计数等要求。非关系存储的专属规则不在本版支持声明内，用户明确要求仍独立遵循。

## 1. 注释语言跟随用户和项目，不能跟随示例随意切换

按以下顺序选择新增和修改的注释语言：

1. 用户明确要求的语言。
2. 当前项目的语言；混合语言项目参考当前模块已有的注释和文档。
3. 项目没有明确语言时，使用宿主或系统已配置的语言：中文环境写中文，英文环境写英文。

不要把 Java 关键字使用英文当成“项目使用英文”，也不要因为对话或规范示例是中文，
就翻译项目中无关的英文注释。同一字段或方法的说明与参数注释使用同一种选定语言，
类型名、API 名和标准术语保留原文。

## 2. 字段、方法和参数完整写多行 Javadoc

- 所有手写字段都写 Javadoc，包括 private 字段、静态字段、常量和枚举常量。
- 所有手写方法都写 Javadoc，包括 private 方法、接口方法、重写方法、getter / setter 和测试方法；构造函数同样处理。
- 所有 Javadoc 使用多行格式，起始标记、说明内容和结束标记各占一行。即使只有一句说明，也禁止使用单行文档注释。
- 每个方法或构造函数的参数用 `@param` 说明实际含义，不只重复参数名；泛型参数用 `@param <T>`。
- 有返回值的方法写 `@return`，说明结果及必要的空值含义；void 方法和构造函数不写 `@return`。
- 需要调用方处理的异常用 `@throws` 说明触发条件。涉及单位、范围或可空性时，写出真实约定。
- record 组件在类型 Javadoc 中用 `@param` 说明；不为给自动生成的成员补注释而复制一套实现。

下面的类只展示完整注释写法。金额校验是该对象实际的业务要求：

```java
/**
 * 以分为单位的订单金额。
 */
final class OrderAmount {
    /**
     * 订单金额，单位为分，不能为负数。
     */
    private final long cents;

    /**
     * 创建订单金额。
     *
     * @param cents 金额，单位为分，必须大于或等于零
     * @throws IllegalArgumentException 金额为负数时抛出
     */
    OrderAmount(long cents) {
        if (cents < 0) {
            throw new IllegalArgumentException("金额不能为负数");
        }
        this.cents = cents;
    }

    /**
     * 获取以分为单位的金额。
     *
     * @return 以分为单位的非负金额
     */
    long getCents() {
        return cents;
    }
}
```

不要只增加“已校验”“批量查询”“不会重复执行”等注释，就声称代码具备该行为。
这些说明必须有真实调用路径支持；新增输入前提不能代替缺失的校验。
修改字段含义、参数、返回结果或异常行为时，同步更新注释，不保留已经失真的说明。

## 3. 方法内只注释核心逻辑，不逐行解释代码

对关键业务判断、计算依据、并发处理或容易被误改的逻辑，用清晰直接的行注释说明原因。
不要给简单赋值、调用和返回添加“设置参数”“调用方法”“返回结果”等重复描述，
也不要在方法内部用 Javadoc 给局部变量逐一写文档。

```java
/**
 * 判断订单是否可以直接取消。
 *
 * @param order 待判断的订单，不能为空
 * @return 订单处于未支付状态时返回 true
 */
private boolean canCancel(Order order) {
    // 已支付订单必须走退款流程，不能直接取消。
    return order.getStatus() == OrderStatus.UNPAID;
}
```

方法说明负责说清契约；方法内注释只补充核心原因，避免把代码翻译一遍。

## 4. Java 实现的构造、复用与类型边界

### 4.1 测试特殊实例在测试类内部构建，不向生产代码增加测试入口

- 生产构造函数必须服务真实业务建模、实际依赖注入或框架实例化要求。
- 禁止仅为单元测试增加生产构造函数、重载、setter、factory、builder 或配置开关。
  改成普通名称、缩小可见性或标注 `@VisibleForTesting`，都不能改变其仅为测试服务的用途。
- 单元测试需要特殊数据、Mock 或替身时，一律在对应测试类内部准备，调用已有的正常构造函数或业务入口。
- 真实生产需求可以带来正常的依赖注入改进；不能为了方便测试，凭空扩展生产对象的状态和可构造方式。
- 测试所需状态若被正常入口拒绝，先确认它是否真实可达。不得为了绕过本应验证的生产校验而制造非法实例；
  模拟历史脏数据或反序列化等真实可达的异常状态时，在测试类内部准备并说明现实来源，不增加测试专用生产入口。
- 校验失败的测试应验证正常入口按约定拒绝输入；不能为了让测试通过，把预期失败改成默认成功。

沿用前面的生产构造函数，在测试类内部创建本用例需要的实例：

```java
/**
 * 订单金额测试。
 */
class OrderAmountTest {
    /**
     * 验证零金额可以正常构建。
     */
    @Test
    void allowsZeroAmount() {
        OrderAmount amount = createAmount(0);
        assertEquals(0L, amount.getCents());
    }

    /**
     * 验证负金额会被正常生产构造函数拒绝。
     */
    @Test
    void rejectsNegativeAmount() {
        assertThrows(IllegalArgumentException.class, () -> new OrderAmount(-1));
    }

    /**
     * 创建当前用例所需的金额实例。
     *
     * @param cents 本用例使用的金额，单位为分
     * @return 通过正常构造函数创建的金额实例
     */
    private OrderAmount createAmount(long cents) {
        return new OrderAmount(cents);
    }
}
```

这里的测试辅助方法属于测试类，生产类不增加“跳过校验”构造函数。
示例中的 JUnit 用法仅用于展示测试准备位置，不要求项目更换测试框架。

### 4.2 先复用已有实现，同一业务规则在合适边界内集中维护

- 新增实现前，先阅读当前模块和已有公共组件中的相关代码、契约及调用方，
  不能只因名称或位置不同就换个名字重写一份。
- 已有实现的业务含义、校验、租户与权限、事务、异常及副作用相符时优先复用。
  方法签名相似不等于适用，不能为复用绕过业务边界。
- 本次涉及的多条路径表达同一业务规则、规则变化必须同步时，集中到一个合适的位置维护，
  不能复制方法后只改名称或常量。抽取后检查所有受影响的实际调用方。
- 选择最小、清晰的抽取边界：同类重复先考虑私有方法；跨类确有复用需求时，
  再使用已有业务归属或共享组件，保留行为和公开契约。
- 外观相似但业务含义或演进方向独立的实现可以保留重复；
  不能仅为减少重复行而增加布尔开关、回调或类型判断，把不同行为塞进万能方法。
- 抽象服务已有的实际使用点，不为假设的未来复用增加通用执行器、基类、策略层级或新依赖。
  不借此开展无关的全仓去重。

已有结算组件应调用已有配送费政策，避免复制一份计算逻辑。下例的 `deliveryFees`
是正常生产构造中已经存在的组件，不要求为示例新建抽象：

```java
/**
 * 按预览使用的同一政策计算确认结算配送费。
 *
 * @param subtotalCents 非负订单小计，单位为分
 * @return 已有配送费政策计算出的费用
 * @throws IllegalArgumentException 小计为负数时抛出
 */
public long confirmedFee(long subtotalCents) {
    return deliveryFees.feeFor(subtotalCents);
}
```

不能用代码行数减少、方法名称或功能测试通过，代替“确实复用已有实现、同一规则有合适归属”的判断。

### 4.3 尽可能避免内部类，确有必要才保留

业务 DTO、结果、策略及 Spring Bean 默认采用已有业务包中的顶级类型，保持必要的最小可见性。
规则覆盖非静态内部类、静态嵌套类，以及嵌套 record、枚举、接口；
加上 static 不能解决职责和定位困难，不能仅为少建文件而藏进 Service 或 Bean。

仅在存在具体必要性时保留嵌套，例如实现确实需要紧密的外层实例封装，或必要的框架、测试结构。
private、代码短、只有一个调用方都不能单独作为必要性。保留的实现仍应小而局部。
确有框架约定时遵循真实要求；这是维护性偏好，不声称 Spring 不支持嵌套组件。

例如业务报价结果通常使用独立源文件中的顶级类型；Java 版本不支持 record 时沿用项目现有类型写法：

```java
/**
 * 业务操作返回的配送报价。
 *
 * @param feeCents 配送费，单位为分
 * @param currency 报价采用的币种代码
 */
record DeliveryQuote(long feeCents, String currency) {
}
```

移动已有嵌套类型可能改变二进制名称、可见性、序列化和依赖装配，必须保持相关契约并服从任务范围。
本规则不授权批量迁移历史类型，也不增加用户审批步骤。

## 5. 禁止逐条查询，关联数据批量加载后在内存中组装

- 禁止在 `for`、`while`、Stream、递归或逐项转换函数中查询数据库。
- 不得把查询隐藏在 getter、工具方法、对象转换或 ORM 懒加载关联中，实际产生的 N+1 同样禁止。
- 把逐条查询搬进线程池、`CompletableFuture` 或并行 Stream，仍然是逐条查询；
  缓存未命中时逐项回库，也不能作为绕过方式。
- 先复用已取得的数据，再收集并去重需要查询的关联标识，执行有界批量查询或合适的 JOIN / 投影，最后在内存中组装。
- 批量方法必须真正执行批量 SQL，不能仅把循环移动到 Mapper、Repository 或公共方法内部。

禁止这样查询：

```java
for (Long userId : userIds) {
    users.add(userMapper.selectById(userId));
}
```

改为一次批量查询。以下示例省略业务类型定义，并以入口已验证租户权限、
非空元素和单批数量上限为前提；实际项目必须能够定位这些验证：

```java
/**
 * 批量查询当前租户的指定用户。
 *
 * @param tenantId 从可信登录上下文取得的租户标识
 * @param userIds 已去重且不超过本次查询上限的用户标识，不能为空
 * @return 查到的用户；未找到任何用户时返回空列表
 */
public List<UserRow> listUsers(long tenantId, Set<Long> userIds) {
    if (userIds.isEmpty()) {
        return Collections.emptyList();
    }
    return userQuery.findByIds(tenantId, userIds);
}
```

`userQuery` 表示项目已有的数据查询入口，不要求新增抽象层。
此例的 `findByIds` 执行一条带租户条件的有界查询，返回普通查询结果对象。
后续 getter 和序列化不能再触发隐藏查询；需要的关联数据应提前加载。

批量化不能悄悄改变结果契约：按请求顺序返回时，在内存中恢复顺序；
去重查询标识不代表可以删除响应中本应保留的重复项；缺失关联按原业务约定处理。
不要在内存查找失败后逐项回库补查，也不能把数据库查询失败伪装为“没有数据”。

## 6. 批量查询也必须有边界，不用无限 IN 或全量加载替代循环

- 校验本次输入数量和结果规模，批量参数上限依据实际数据库限制和业务预算确定，不随意套用固定数字。
- `findByIds` 一类必需的正向包含条件为空时，直接返回空结果，不执行该次查询，
  不生成空 `IN`，也不能悄悄删除必需的包含条件。
- 排除集合为空时，按“不排除任何项”的既有契约处理；项目明确约定可选筛选为空表示不筛选时，
  保留该语义，不能一律改成空响应。所有分支仍保留租户、权限和结果数量边界；
  空集合不能成为删除必需访问条件的理由。
- 查询保留适用的租户、权限、时间、状态等范围，返回本次需要的字段。
  不能先查全量，再在 Java 中分页或过滤权限。
- 分页数量有上限，排序能处理相同排序值；返回规模受控不代表扫描成本已经受控。
- 大规模导出或历史扫描确需多轮查询时，复用用户已经授权的范围、批大小、次数预算、终止条件及一致性要求，
  包括适用的项目约定。范围内的局部修改不新增审批；缺失决定影响本次实现时才澄清，
  扩大已经授权的范围或预算前取得同意。不得把逐条查询改名为“分批”，绕过禁止逐条查库的要求。

下面以支持 LIMIT 的 SQL 数据库示意单页查询，问号表示绑定参数；
实际 SQL 方言和参数传递方式由项目采用的数据库及访问组件决定：

```sql
SELECT id, status, created_at
FROM orders
WHERE tenant_id = ?
  AND status = ?
  AND id > ?
ORDER BY id
LIMIT ?
```

最后一个参数对应已校验的 `pageSize`，租户参数来自可信上下文。该示例说明单次查询的范围，
不表示已验证索引有效，也不自动提供跨页快照一致性。

## 7. 按实际 SQL 判断一次操作的成本，不按方法名判断

写数据访问代码前，沿实际调用链确认：

- **执行几次**：包括主查询、分页 count、权限检查、关联加载、序列化和可能的兜底补查。
  一个 Repository 方法不一定只执行一条 SQL；重复获取相同数据应先复用已有结果。
- **访问多少数据**：同时看输入规模、扫描范围、返回行数和字段宽度，不能只看最终返回几条。
- **怎样影响表**：核对过滤、排序、索引访问方式、JOIN 行数放大，以及适用的锁范围和连接占用。
  不因返回十行就判断只扫描十行，也不因出现索引名称就宣称开销很小。

例如“查询订单列表并补齐客户名称”，先设计为有界订单查询、一次去重后的客户批量查询、
纯内存组装。只有真实 SQL 证明没有额外 count、懒加载或兜底查询时，才能报告“最多两次查询”。
不能仅把方法命名为 `batchQuery`，或者在注释中写“两次查询”，就当作完成了优化。

有执行计划、SQL 计数或实际测量时，说明它们支持的具体结论；没有这些证据时，
把预期次数和成本判断说清楚，不声称已经实测。普通 Mapper 调用次数断言不能证明不存在隐藏 SQL。
改动应解决本次查询问题，不自动给所有条件添加索引，也不重构无关的数据访问层。

## 8. JPA：检查持久化机制产生的隐式行为

只有本次修改或审查影响 JPA 映射、实体构造、生命周期、查询或相关持久化调用时读取本节。
Java 声明沿用第 1—4 节，数据库次数、范围和结果契约沿用第 5—7 节，不在这里重复定义。
只有确认实际使用 Hibernate ORM 及其版本，才套用 Hibernate 专属结论；
Hibernate Validator 不等于 Hibernate ORM。

- 调整关联加载后，检查遍历、getter、DTO 转换和序列化是否仍触发逐条 SQL。
  把关联改为 LAZY 或加上 EntityGraph，不足以证明消除了 N+1；不统一改成 EAGER。
- 组合集合 fetch join 与分页时，核对实际 SQL、分页位置、总数查询和结果数量。
  不把 Java 返回了 Page 当成数据库已经执行了有界分页，也不忽略 JOIN 后的数据放大。
- 事务内拿到受管理实体后，不为拼装响应而随意修改其字段或关联。
  脏检查可能把这些修改同步到数据库，不能以“没有调用 save”为依据宣称没有写入。
- 新增或修改 cascade 时，核对它传播的具体操作是否符合业务意图。
  对 REMOVE、包含删除传播的 ALL 及 orphanRemoval，额外确认父对象是否拥有相应子对象的生命周期。
  不为方便映射而复制级联删除配置，也不把非删除传播一概当成生命周期归属声明。
- 使用 saveAll 等 API 后，分别核对 SQL 语句数、JDBC 批处理和数据库往返次数。
  方法名或 batch_size 配置不证明批处理有效；例如 Hibernate 6.6 的 IDENTITY 插入不使用 JDBC 插入批处理，
  这一结论不能直接扩展到其他实现或未核对的版本。

JPA 实体实际需要的框架构造函数可以保留，不属于“测试专用构造函数”。
下面仅展示这一边界，实际注解包名匹配项目版本：

```java
/**
 * 订单持久化实体。
 */
@Entity
public class OrderEntity {
    /**
     * 订单唯一标识。
     */
    @Id
    private Long id;

    /**
     * 供 JPA 持久化实现创建实体实例。
     */
    protected OrderEntity() {
    }
}
```

这里的构造函数有真实框架用途。测试仍不能额外增加跳过校验的构造函数或其他生产入口。
本节不规定全部项目必须使用 JPA，也不自动切换持久化实现、关闭 OSIV 或引入新的框架。

## 9. MyBatis：核对 Mapper、SQL 和结果映射的实际绑定

只有本次代码实际使用 MyBatis Mapper、映射 XML、SqlSession 或其调用链时读取本节。
同名 Mapper 不足以证明使用 MyBatis；识别方法见插件设计稿。
修改已确认的 MyBatis 映射 XML 时遵循数据访问与 MyBatis 规则，不向 XML 添加 Java Javadoc。
JPA 映射或持久化 XML 按实际 JPA 机制选择规则，涉及 SQL 行为或成本时再应用共通数据访问要求；
其他 XML 不因文件扩展名而自动获得持久化规则。

- 修改 Mapper 方法、参数或 XML 时，一起核对 namespace、statement id、Param 名称、foreach 的 collection
  和结果字段映射。不能只把 Java 编译通过当成 SQL 绑定正确。
- 普通值使用 `#{}` 绑定；`${}` 是文本替换，不直接接收用户输入。
  确实需要动态表名、列名或排序方向时，从可信允许列表选取，不能通过字符串替换修补参数绑定错误。
- 调整动态条件时，检查空集合、null 和缺省值的实际 SQL，不能因跳过条件而扩大查询范围。
  输入上限、空集合处理和权限范围仍按第 5—7 节落实。
- association / collection 的嵌套 select、延迟加载或转换过程中触发的补查，都计入实际 SQL 次数。
  不能把 Mapper 方法只调用一次当成没有 N+1。
- 配置分页、批量执行或缓存时，核对当前项目实际启用的插件和执行方式。
  分页插件可能增加 count，BATCH 等执行模式不代表一条 SQL；不为满足规则直接改变全局执行器或插件配置。

示例中的方法位于 `example.UserMapper`，Param 来自 MyBatis；UserRow 是已有的普通查询结果对象。
入口已按第 5—6 节处理空集合、数量上限和权限，XML 不能再次漏掉租户条件：

```java
/**
 * 批量查询租户内指定用户的展示信息。
 *
 * @param tenantId 从可信登录上下文取得的租户标识
 * @param userIds 已验证的非空标识集合，数量不超过查询上限
 * @return 查到的用户展示信息；未匹配时返回空列表
 */
List<UserRow> selectByIds(
        @Param("tenantId") long tenantId,
        @Param("userIds") Set<Long> userIds);
```

```xml
<mapper namespace="example.UserMapper">
    <select id="selectByIds" resultType="example.UserRow">
        SELECT id, display_name AS displayName
        FROM users
        WHERE tenant_id = #{tenantId}
          AND id IN
        <foreach collection="userIds" item="userId" open="(" separator="," close=")">
            #{userId}
        </foreach>
    </select>
</mapper>
```

这是参数与映射一致性的最小示例，不是整套 Mapper 模板。
MyBatis-Plus 等扩展首版不提供专属规则；确实经过基础 MyBatis 的部分仍按已确认机制检查，
不能把扩展框架的 Wrapper、拦截器和逻辑删除行为当成已经覆盖。

## 使用边界与参考

这份规则覆盖用户明确的注释偏好、测试与生产代码边界，以及数据访问中的具体风险。
不会因为引用外部资料，就追加整套命名、泛型、Optional、金额、时间、资源关闭或框架教程。
规则是否能减少实际失误，需要后续用真实编码任务验证；本文不宣称已经测得改进效果。

- [Java 文档注释与标准标签](https://docs.oracle.com/en/java/javase/21/docs/specs/javadoc/doc-comment-spec.html)
- [MyBatis 参数绑定、关联映射与嵌套查询](https://mybatis.org/mybatis-3/sqlmap-xml.html)
- [Spring Data 查询返回类型与分页成本](https://docs.spring.io/spring-data/jpa/reference/data-commons/repositories/query-methods-details.html)
- [Hibernate fetch join 与分页行为](https://docs.jboss.org/hibernate/orm/7.0/querylanguage/html_single/Hibernate_Query_Language.html)
- [Hibernate 持久化上下文与 JDBC 批处理](https://docs.hibernate.org/orm/6.6/userguide/html_single/)
- [Jakarta Persistence 实体与关联生命周期](https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2.html)
