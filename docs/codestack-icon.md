# CodeStack 图标制作记录

正式图标为 [codestack.png](../plugins/ai-code-stack-standards/assets/codestack.png)，
作为普通白名单资源供三宿主包共用。Codex 的 logo / composerIcon 引用本地 PNG；
ZCode 的市场展示声明使用固定源码提交的 raw PNG 地址，沿用 CodeVow 的接入方式。

生成方式：内置 imagegen，日期 2026-10-19。先生成深蓝堆叠图标，再以该图为参考微调。
根据用户选择保留同系列深蓝底和三层代码卡片，将正面淡紫括号调整为冰蓝色，
前层卡片边缘调整为青蓝色。CodeVow 保持原有淡紫括号与绿色校验勾，CodeStack
通过堆叠轮廓和蓝色强调保持区分。暖色探索版本未采用，不进入最终发行资源。

最终生成结果原样复制，未裁剪、重采样或转成 SVG。实际图像为 1254 × 1254 PNG，
RGBA，1193362 字节，圆角外沿透明。首轮提示词要求 1024 × 1024；实际尺寸以文件为准。

## 首轮生成提示词

```text
Use case: logo-brand. Create one original polished square PNG app icon for CodeStack, a plugin that gives LLM coding assistants a small set of project conventions across multiple languages and technology stacks. Match the family of a clean premium developer-tool icon: a deep navy (#0F172A) rounded-square tile, generously padded with a truly transparent surrounding canvas, subtle soft finish, crisp geometric forms. Central symbol: three broad rounded code cards stacked in a compact balanced vertical arrangement, slightly overlapping to clearly read as a stack. The foremost card bears only two thick simple opposing code chevrons, not any lettering. Use lavender (#A5B4FC) for the code chevrons, mint (#34D399) and teal (#0F766E) as restrained accents on the layer edges, enough separation to read clearly at 48 pixels. Keep the mark bold and minimal, approximately centered and large within the tile. One flat front-facing icon; no perspective, no tiny details, no text or letters, no checkmark, no badges, no platform logos, no Java or framework logos, no robots, no brains, no circuitry, no watermark, no mockup. Render a single square 1024 by 1024 PNG with an alpha channel. Keep the outside of the rounded navy tile truly transparent.
```

## 最终微调提示词

参考图为首轮自行生成的深蓝 CodeStack 图标。

```text
Make a subtle identity refinement of this CodeStack app icon. Preserve the original composition, the deep navy rounded-square tile, the same three overlapping code cards, their geometry, proportions, padding, soft finish and true transparent outer background. Do not redesign the icon. Only adjust accent colors slightly to distinguish this icon from CodeVow while keeping the same product family: change the prominent lavender code chevrons on the foremost card to crisp pale ice blue (#7DD3FC); give the foremost card edge a restrained cyan-blue (#38BDF8) highlight. Keep the rear teal and mint layer edges close to the original but slightly cooler. Keep the navy card surfaces. Keep the chevrons large and bold with the same shape, and keep all three layers visibly separate. No orange or amber, no new symbols, no checkmark, no text, no letters, no platform logos, no extra decoration, no added tiny details. This should look like the same first icon with carefully differentiated blue/cyan accents, not a new design. Preserve transparency outside the rounded tile and output a square PNG.
```

## 来源和校验

这是为 CodeStack 新生成的原创标识，没有引用外部图片、平台或框架 Logo，
沿用插件现有 MIT 许可声明。最终 PNG SHA256：

```text
620d80de95511cb2efb62334349aa9f9e5b59eba24aa3ce45b90104cdb37c694
```

已检查 PNG 结构、像素解码和透明通道。资源/包检查、URL 可访问性与真实宿主显示
是不同的验证层级；原始图标和配置不表示宿主验收或正式市场发布已经完成。
