# Reed：R 形态平衡修订记录

日期：2026-10-28。用户已区分插件图标与页面字标用途，本轮保留样式并调整 R 的重心。主记录见[视觉升级](2026-10-28-reed-visual-refinement.md)。本记录中的图形生成使用内置 Image Gen；随后用户确认 v2 并授权制作前端 Demo。

## 当前资产

- [插件图标 v2](assets/2026-10-28/reed-plugin-icon-v2.png)
- [页面字标 v2](assets/2026-10-28/reed-wordmark-icon-eed-v2.png)
- [页面放置效果](assets/2026-10-28/04-native-light-balanced-brand.png)

v2 是本轮对外的设计修订号；中间几何试稿没有作为当前资产入库。最终插件图标经过几何修订与切口清理，再用于字标与界面装配。用户已明确确认本版图形，并要求开始 Demo。前端直接复用该版资产，当前资产不等于已安装、注册商标或公开发行。

## 实际生成提示

### 1. 几何平衡

透明背景；参考原独立 R 与原字标。

```text
Use case: precise-object-edit / logo refinement. Asset: standalone plugin icon for Reed. INPUT IMAGE1 is the current approved-style abstract woven R icon to refine. INPUT IMAGE2 is its current Reed wordmark context. User accepts the overall style and use system but specifically finds the R optically unbalanced. This is a careful geometric redesign of the SAME visual family, not a new brand concept. Produce ONE revised symbol, no variations sheet, no text.
Keep monochrome dark graphite #2E353B, gently rounded broad bands, R recognition and a single restrained woven over-under cue. Correct the optical imbalance:
- Establish a coherent left vertical skeleton. Upper and lower left portions share the same vertical axis and approximately the same stem weight, so they feel like one R rather than three floating pieces. Avoid a short detached curved left foot.
- Reduce the diagonal leg's ink mass, not just its tip length. Make it slightly lighter than the vertical stem, start the crossing slightly higher, and pull the lower-right endpoint inward. It must not drag the entire symbol down-right or extend far beyond the bowl's right edge.
- Left stem and diagonal leg land on the same optical baseline; use softly flattened rounded endings instead of huge pill/blob terminals. Maintain near-square typographic proportions, roughly0.85 width to1 height, NOT a stretched wide R.
- Open and balance the upper bowl's inner counter, keep the top band no heavier than the supporting stem. The bowl is compact, comfortably proportioned to the lower half.
- Unify outer curvature and cut language. Preserve only one clean broad over-under separation. Remove sharp narrow wedge fragments and hairline slits; the internal opening must survive a24px icon rendering. No cluttered repeated cuts.
Optical balance is the goal, not mirror symmetry: it must remain a distinctive R. Do not revert to a plain font R, generic infinity, knot, arrow, leaf or robot. Do not add a surrounding tile, circle or border.
Strictly FLAT single ink shape, no gradient, sheen, shadow, 3D, texture, colored edge or lighting. Crisp vector-like edges, generous negative space, professional native desktop identity. Current date2026-10-28 irrelevant to artwork, no dates/text.
Target1024x1024 canvas, genuine transparent alpha background. Symbol occupies about64–68% of canvas, visually centered by ink mass with generous safety margins. Plugin-icon placement is centered independent of future wordmark baseline; do not include eed in this output. No baked checkerboard or opaque white square. One symbol only.
```

### 2. 交织切口清理

透明背景；参考上一几何试稿，生成当前插件图标。

```text
Use case: precise-object-edit / final local refinement of a logo. INPUT is the already optically rebalanced Reed R symbol. Keep its overall proportions, left support, shorter diagonal leg, matching baseline, upper counter, rounded-band vocabulary and solid dark graphite #2E353B. User accepts this style; do NOT invent another concept.
Make only one small optical improvement: at the upper-left woven crossing, eliminate the needle-point pinched slit. Express that SAME single over-under crossing using a clean negative-space channel of stable readable width, with softly blunted endings rather than sharp wedge tips. At24px symbol size the gap should remain visible around1px, not disappear into a hairline. Keep only one restrained crossing, do not add extra slices, outlines, detached chips or corner cuts. Preserve the large bowl counter and the now-balanced legs. Do not thicken the lower-right leg or stretch it again. This is optical cleanup, not a letter redesign.
One standalone plugin icon, no eed, no other text, no tagline. Genuinely transparent alpha background. Target1024x1024 square canvas, original mark occupancy and optical centering with generous safe margins. Flat monochrome, no gradients, sheen, shadows, lighting, textures, 3D, tile or surrounding shape. Clean vector-like silhouette and strong negative space. Return only the revised single R symbol.
```

### 3. 配套字标

透明背景；参考当前插件图标与原 eed 字体组合。

```text
Use case: logo-brand / wordmark refinement. INPUT IMAGE1 is the NEW optically balanced Reed standalone plugin R symbol. INPUT IMAGE2 is the earlier Reed wordmark showing the approved eed typography and overall composition. Make one revised transparent horizontal wordmark for the top-left corner of the opened Reed page.
Use exactly the NEW symbol silhouette from image1 as the FIRST LETTER, followed by literal lowercase "eed". Visible reading is Reed. Do not add any extra capital R, full Reed text, icon tile or duplicated symbol. The only literal letters are eed.
Keep the old eed type style: clean modern humanist sans-serif, medium500, open e counters, upright d, natural tracking. Replace only the R shape and refine optical alignment, do not choose a decorative new font. Normalize the symbol's ink bounds independent of its square transparent canvas, then align the R's bottom with the letter baseline and top close to d's ascender (optical overshoot no more than about4%). It must NOT loom taller or heavier than the text. Keep R-e gap typographic and tight but clear, so symbol and letters read as one word. Match stem weight as closely as the distinct letter geometry allows.
All elements solid graphite #2E353B, flat, with no gradient, sheen, shadow, texture, 3D or backdrop. Keep the new R's restored left support, inward shorter diagonal, open counter and stable over-under gap; do not redraw it as the old overweight diagonal. Preserve its optical balance.
Target1536x512 horizontal transparent alpha canvas with generous margins and the single compact lockup centered. No tagline, no dates, no annotations, no device mockup, no comparison sheet. Export only the single revised symbol+eed wordmark, genuinely transparent background without a white rectangle or baked checkerboard.
```

### 4. 页面放置效果

非透明整页；参考原界面与当前配套字标。

```text
Use case: precise-object-edit / UI identity replacement. Image1 is the accepted Reed native-light app layout. Image2 is the newly optically balanced R+eed wordmark. User has defined standalone R as plugin icon and R+eed as opened page's top-left identifier.
Replace ONLY image1's top-left brand lockup with the exact visual from image2, scaled as a compact24–26px-high wordmark at the original position. The new R shape has more stable left support, reduced shorter diagonal leg, balanced counter and clean crossing. Preserve those features, do not revert to the old long heavy diagonal. Use [R symbol]eed, no extra literal R, no duplicated full Reed text, no tagline. Keep natural tight R-e optical spacing and matching baseline/ink weight; glyph must not be taller or bolder than the rest of the word. Solid dark graphite, transparent mark on the existing light-gray sidebar, no extra tile, shadow or gradient.
Target1679x937 same app viewport as image1. Everything outside the small brand area stays unchanged: full three-pane geometry, text sizing, sidebar navigation and project, neutral white/gray surfaces, blue-gray accents, top-right 系统 theme selector, REQ-1042 task and its title, current design pending acceptance, document content and V2, review actions, related document and ended Codex conversation, next-stage workspace not created, local saved sample status and dates. Do not rebuild, simplify, add features or change product states. Current actual date2026-10-28; preserve historical sample dates.
One crisp app screenshot only, no browser/device frame, no caption, no comparison. This is a visual composition for user review, not a functional app or claim of native host integration.
```
