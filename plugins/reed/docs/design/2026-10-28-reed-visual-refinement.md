# Reed：原生浅色升级与图标字标组合

日期：2026-10-28。性质：设计资产与生成记录。用户随后确认 v2，前端 Demo 已采用该基准；正式插件及真实系统接入仍未实现。

用户选定最新浅色三稿的第一张「原生留白」，并明确独立 R 用于插件图标、「R 图形＋eed」用于页面左上角。整体读作 **Reed**，不设中文名，副标题为 **Many agents. One flow.**。用户认可整体样式，同时指出 R 重心不平衡；平衡修订 v2 已获用户确认，当前 Demo 直接复用该版图标与字标。

界面保持中性白、浅灰导航、墨色文字、克制灰蓝标识和深色主按钮；系统／浅色／深色选择继续保留。早先古铜方案只作历史交互场景参考。

## 1. 当前组合与页面

![平衡修订 v2 的当前浅色装配稿](assets/2026-10-28/04-native-light-balanced-brand.png)

- [所选原始浅色稿](assets/2026-10-28/01-selected-native-light.png)
- [透明插件图标 v2](assets/2026-10-28/reed-plugin-icon-v2.png)
- [透明页面字标 v2](assets/2026-10-28/reed-wordmark-icon-eed-v2.png)
- [当前界面装配稿 v2](assets/2026-10-28/04-native-light-balanced-brand.png)
- [上一版独立图标](assets/2026-10-28/reed-mark-candidate-v1.png)、[上一版组合](assets/2026-10-28/reed-wordmark-icon-eed-v1.png)、[上一版装配](assets/2026-10-28/03-native-light-icon-eed.png)
- [上一版图标＋完整 Reed 的过渡稿](assets/2026-10-28/02-native-light-with-mark.png)

本轮只调整左上角品牌组合，主体导航、阶段、审阅动作、文档和原生会话入口沿用所选稿。画面中的业务数据、时间与状态为样本，不是实际服务结果。

## 2. 图标与字标规格

交织带状结构构成抽象 R，呼应多 Agent 工作汇入流程。组合时图标作为第一个字形，后面只印小写 eed；不能成为图标＋Reed 或 RReed。

v2 的几何收敛：上下左笔共享更清楚的轴线，缩减斜笔面积并内收右下端；两侧落脚更接近同一视觉基线，上碗保留开阔内孔；交织切口消除针尖式细缝。此处为设计判断，尚非矢量轮廓测量或真实宿主的小尺寸测试。

| 场景 | 设计目标 |
| --- | --- |
| 插件图标 | 独立 R，方形透明画布，按墨量光学居中；不把完整字标压入图标位 |
| 展开导航品牌 | 组合高度约 24–26px，符号与 d 的字顶、文本基线光学协调 |
| 符号与首个 e | 约 1–3px 光学间距，作为一个词阅读，不沿用独立图标与标签的 8px 间距 |
| 小写 eed | 清楚的现代无衬线、中等字重、自然字距；符号和字母重量接近 |
| 导航收起 | 可仅显示独立 R 符号，24px 外框，保留内部负形 |
| 颜色 | 浅色为墨灰单色；深色需另做浅色单色映射，不直接沿用深色位图 |
| 名称与无障碍 | 文本、搜索、无障碍名称保持 Reed；eed 只属于视觉组合的后半部分 |
| 副标题 | 用于欢迎、关于和介绍材料，日常任务页不额外堆副标题 |

当前为透明 PNG 位图资产，尚无矢量母版。Demo 已检查页面字标和深色反相；正式插件在 16/20/24px、多像素密度下的清晰度仍须按真实宿主验收。生成图不等于字距测量或逐像素一致性证明；图形标识尚未进行正式注册或近似检索。

## 3. 保存与范围

图形制作阶段使用内置 Image Gen，图标和字标生成时启用透明背景，没有额外图像服务或手工 SVG 追踪。用户随后授权前端实现；源码位于 `plugins/reed/prototype/`，图标与字标复制到其 `public/assets/`。没有插件安装、Git 提交或市场发布。所有当前引用的设计资产均已复制到 Reed 产品目录。

交互与系统颜色要求见[交互设计](2026-10-28-reed-interaction-design.md)。其他视图已在 Demo 中按新基准延展，当前装配稿不替代真实宿主或操作验收。

## 4. 实际生成提示

### 4.1 独立交织 R 图标

工具：内置 Image Gen。transparent_background=true；新生成，无参考图。

```text
Use case: logo-brand. Asset type: one candidate compact icon for Reed, a local-first developer workflow workbench. Brand name Reed, chosen tagline "Many agents. One flow." The product connects tasks, native Agent conversations and development branches into a coherent workflow. Create only the standalone symbol, NO wordmark, NO text, NO tagline.
Design a restrained original woven-flow monogram: two broad, softly folded continuous bands meet through one small, intelligible over-under crossing, forming a compact upright abstract R-like silhouette with one open counter and a subtle diagonal leg. The hint of R is secondary to a clear flowing woven structure. Exactly one elegant, distinctive mark. Large open negative spaces; balanced mass; blunt gently rounded ends; crisp clean flat silhouette. Strong enough to remain recognizable when placed in a24px UI icon box, actual glyph18–20px. Make internal openings generously sized, avoid thin line details and complicated knots. Use only one solid dark graphite color #2E353B; absolutely no secondary color, outlines, shading, lighting, gradients, 3D, texture, glow, drop shadow or enclosing square/circle. Not an infinity loop, generic chain-link, atom, sparkle, leaf cluster, robot, braid of many strands, or ornamental knot. Do not copy a familiar commercial mark.
Target1024x1024 transparent canvas, symbol centered with generous transparent breathing room, symbol occupying about64% of square. Genuinely transparent background (alpha), NO white square, NO checkered backdrop baked into image. Smooth high-quality edges and optical balance, vector-friendly flat construction, professional native desktop identity. This is a visual design candidate rather than a final registered logo. Output only one icon, no alternatives sheet, no mockup, no labels.
```

### 4.2 图标＋完整 Reed 的过渡装配

工具：内置 Image Gen。transparent_background=false；编辑，依次参考所选浅色稿与独立图标。此组合已被下一版替代。

```text
Use case: precise-object-edit. Asset type: exact Reed app screenshot with one logo insertion. INPUT IMAGE1 is the USER-SELECTED new light UI, the first displayed option in the latest ideation set. It is the edit target and MUST remain unchanged except the small top-left brand area. INPUT IMAGE2 is the Reed transparent standalone R/weave candidate mark to insert, not an image to redesign.
Target dimensions1679x937, preserve original natural viewport, all layout proportions, typography, text, content, white/gray surfaces, subtle blue-gray links, stage navigation, action buttons and right inspector. No style exploration. No perspective mockup or outer frame. Current date2026-10-28; preserve original sample timestamps.
Insert the EXACT icon from image2 at the top left immediately before the existing Reed wordmark. Use a24px square optical icon box at this image's visual scale, visible mark roughly20px tall, same dark graphite tone as Reed text or marginally lighter. Keep8px breathing room between visible mark and wordmark, align optical centers. Preserve left margin30px of the original brand area; move Reed wordmark right only as needed to fit the icon. No enclosing colored square, circle, button, badge, shadow, gradient or extra label. Keep generous empty space after the compact brand lockup. Do not enlarge the logo or turn it into a decorative hero.
Do not add the tagline on this daily work screen. Brand remains Reed with no Chinese product name. Do not reproduce the reference icon's transparent margin as an opaque box; composite only the mark. Match its interwoven R-like silhouette, do not replace it with a generic R, infinity loop or sparkle.
Everything else is invariant: sidebar entries 待我处理3, 任务 selected, 会话, 分支 and 成员中心 project; breadcrumb REQ-1042 with 云效·已同步; current 设计·待验收; title 成员导入失败后自动补偿; reading content 补偿方案·V2; primary 确认设计; secondary 要求修改; related document and ended native conversation; next-stage unprepared workspace. Top-right 系统 remains for system/light/dark mode. No new features, removed links, changed stage acceptance, layout simplification, font enlargement or altered state. One premium crisp production screenshot, only addition is the restrained icon next to Reed.
```

### 4.3 图标代 R，后接 eed

工具：内置 Image Gen。transparent_background=true；依次参考独立图标与过渡装配稿。

```text
Use case: logo-brand. Asset type: compact Reed wordmark lockup, genuine transparent PNG. The user APPROVED the symbol in reference image1 and now explicitly wants the symbol to replace the capital R, followed by the lowercase letters eed. Reference image2 shows the app visual language and old icon-plus-full-Reed combination to improve. Preserve the approved symbol silhouette.
Create ONE horizontal typographic lockup whose visible reading is Reed: [approved abstract woven R symbol] + "eed". IMPORTANT the only literal letters rendered are eed. Do not render an extra R, Reed, REED, or another brand string. No tagline. No alternate versions sheet or presentation captions.
Refine the typography and optical alignment: symbol is the first letter of the word, not a separate app badge. Use clean modern humanist sans-serif lowercase eed, medium500 weight, open counters, smooth ordinary e shapes and an upright d. No custom decorative ligatures in eed, no serifs. Match visual weight between symbol strokes and the letter stems. Set the symbol's apparent top height close to the d ascender, align its bottom with the baseline optically. Tight but breathable transition from symbol to first e, roughly one-quarter of an e's inner counter width. Letters eed have restrained natural tracking. At a24px high UI wordmark, the whole mark must read as a single name, not icon then separated label.
Solid dark graphite #2E353B for symbol AND all letters, genuinely flat no lighting or tonal gradient. Keep the symbol's woven crossing, open negative space and diagonal leg intact. Do not redesign it as a generic printed R, infinity, arrow or leaf. No containing tile, rectangle, circle, outline, shadow, glow, texture, 3D, scenery or branding mockup.
Target1536x512 transparent canvas, horizontal lockup centered with ample transparent margins. One group, full visible glyph height roughly270px, natural width, no clipping. Background truly transparent alpha, not a baked checkerboard or white rectangle. Professional vector-like edges and polished optical balance. Output only the single symbol+eed wordmark.
```

### 4.4 当前界面装配

工具：内置 Image Gen。transparent_background=false；依次参考过渡界面与图标＋eed 组合。

```text
Use case: precise-object-edit / wordmark replacement. INPUT IMAGE1 is the accepted Reed native-light app screen, with an approved abstract R symbol followed by the full word Reed. INPUT IMAGE2 is the new approved-symbol-plus-eed wordmark composition to insert. User explicitly wants the icon to function as the R in Reed. The resulting visible brand must be [R symbol]eed, reading Reed, with NO extra capital R.
Target1679x937 same native viewport as image1. Modify ONLY the top-left brand lockup: replace the old separate icon + literal Reed text with the exact horizontal symbol+eed composition from image2. Treat the symbol as the first letter, keep the gap from symbol to first e narrow and typographic rather than an8px app-badge gap. Overall lockup apparent height about25px, positioned at original left margin30px, optically vertically aligned around existing brand baseline. Keep silhouette and letter shapes faithful. Use solid dark graphite on the sidebar, no gradient, colored tile, shadow, enclosing outline, extra text or tagline. Do not add text R, Reed or eed elsewhere in the logo area. The logo must read as one name at normal UI scale, neither too large nor squeezed.
Everything outside the brand area remains invariant: neutral white main canvas, light gray sidebar, all typography/layout/columns/widths, quiet blue-gray accents, top-right 系统 menu, sidebar 待我处理3,任务selected,会话,分支,成员中心; task REQ-1042 and title 成员导入失败后自动补偿; compact stage navigation 需求/设计待验收/开发/验证; design document 补偿方案 V2 with unchanged body; 确认设计 and 要求修改 actions; related file and ended native conversation; next-stage unprepared workspace and 本地已保存. No redesign, no removed controls, no new features, no changed content, no native status claims. Current date2026-10-28, keep source sample timestamps unchanged. Only change the brand's symbol/text composition.
Output one crisp premium native-like full-app screenshot, no device/browser chrome, no comparison boards or editorial caption.
```

## 5. 验证边界

图形阶段核对文档、本地引用、图像格式和透明通道，并查看独立资产及装配稿。后续 Demo 已做浏览器操作与同画面对照，记录见[视觉验收](../../prototype/design-qa.md)。已实现本地模拟导航、主题与阶段流转；不声明四端原生执行、真实云效同步或 Git 工作区已接通。
