# Skybear UAT Field Inventory (Phase 0)

**Source**: `https://test01.travel.webuy.ren` (ittest 用户), DB `webuy_tourt` on `test.tourt.mysql.webuy.ren:3381`.
**Date**: 2026-05-07
**Reference TourType**: `WBMXMN` (id=595, pax_type=1 G-Group, travel_days=7, area_id=337)
**Reference wt_travel**: id=149
**Reference wt_tour 样例 (Edit page)**: id=2090 (`01WBTUKW04/24GF`)

---

## URL 模式

| 页面 | URL |
|---|---|
| Login | `/#/login` |
| Dashboard | `/#/dashboard/index` |
| Package List | `/#/packageAirlineMaintenance/packageList` |
| Edit Package (wt_tour) | `/#/packageAirlineMaintenance/editPackage?id=<wt_tour.id>&type=edit` |
| Package Content Mgmt | `/#/packageDisplayMgmt/packageContentMgmt` |
| Edit Display Detail (wt_travel) | `/#/packageDisplayMgmt/editDisplayDetail?id=<wt_travel.id>&type=edit` |

URL 是 hash 路由 (Vue SPA)。**SPA 不监听 hash 变化**——直接 navigate 改 URL 后必须 `location.reload()` 才会重新拉数据。

---

## Step 2 — Create Package（创建 Tour Code）

**两步流程**，不是一步：
1. 在 Package List 页点 `Create Package` 按钮 → 弹 **Modal "New Tour Code"**（基本信息）→ 点 `Save`
2. Modal Save 后**自动跳转**到 Edit Package 页（带新 wt_tour.id 的 URL）→ 填价格 + 航班 + Cost → 点 `Submit`

### 2.1 Modal "New Tour Code"

| Section / Field | UI 类型 | Required | wt_tour 字段 | 备注 |
|---|---|---|---|---|
| **Tour Code** | 3 联组件 | ✓ | `tour_code` | 格式提示 `MMTTTTTTTTTXXXXXXX` |
| ├─ MM | 下拉 (01-12) | ✓ | (前 2 位) | 月份 |
| ├─ Tour Type | autocomplete textbox | ✓ | (中 N 位) | 输入 type_code，自动填 type_name + Region + Pax Type |
| └─ 后缀 | textbox | ✓ | (尾部) | 例如 `10/26MF`，DD/YY+AIRLINE |
| **Tour Type** | readonly textbox + textbox | ✓ | (联动) | type_code + type_name |
| Tour Name | textbox | ✓ | `tour_name` | 默认会从 type_name 拉，可改 |
| Region | readonly | ✓ | `area_id` 联动 | 从 wt_tour_type.area_id |
| Description | 2 行 textbox | ✗ | `tour_remark`, `tour_remark1` | 自由文本 |
| Departure Date | date `DD/MM/YYYY` | ✓ | `departure_time` | |
| Travel Days | number | ✓ | `travel_days` | 默认从 type 拉 |
| Return Date | date `DD/MM/YYYY` | ✓ | `return_time` | |
| Pax Type | readonly 下拉 | ✓ | (联动 wt_tour_type.pax_type) | |
| Quantity | number | ✓ | `inventory_num` | |
| Paym Due Days | number | ✗ | `pam_due_days` | **默认 21** |
| Paym Due Date | date | ✗ | `paym_due_date` | |
| TM/TL | textbox（自由文本，**非下拉**）| ✗ | `tl_tm_name` | 直接写 leader 姓名（不关联 leader 表）|
| Tr Remarks | 3 行 textbox | ✗ | `tour_remark`, `tour_remark1`, `tour_remark2` | |
| OP Remark | 2 行 textbox | ✗ | `op_remark1`, `op_remark2` | |
| [Save] | 蓝按钮 | — | — | 保存并跳到 Edit |
| [Cancel] | 灰按钮 | — | — | |

### 2.2 Edit Package 页（Modal Save 后自动跳到这里）

URL: `editPackage?id=<wt_tour.id>&type=edit`

| Section | 字段 | UI | wt_tour / wt_tour_price 字段 |
|---|---|---|---|
| **Tour Code** 顶部 | Tour Code (readonly) / Tr Status (下拉，默认 Pending) / Tour Type (readonly type_code+type_name) / Tour Name / Region (readonly) / Description (2 行) / Departure Date / Travel Days / Return Date / Pax Type (readonly) / Quantity | text/date/select | 同 Modal |
| **Flight Itinerary** | 多行表格 | 每行: date / flight_no / from / to / dep_time(HHMM) / arr_time(HHMM) / arrival_day(0/+1) / seat_code(下拉默认 G) / flights_status(下拉默认 RQ) + [Add New][Delete] | `wt_tour_flight_itinerary` 多行 |
| **Tour Fare** (price_type=1) | 7 列 sellPrice/costPrice：SGLfare / TWNfare / TRPFare / ChdHfTwn / ChdWEbed / ChdWOBed / InfFare + [Set Tiered Price] | number | `wt_tour_price` (price_type=1) |
| **Land Tour** (price_type=2) | 6 列 sellPrice/costPrice：GroundSGLFare / GroundTWNFare / GroundTRPFare / GroundChdHfTwn / GrChdWEBed / GrChdWOBed | number | `wt_tour_price` (price_type=2) |
| **Additional Charges** (price_type=3) | AirportTaxes/FuelSurcharge | number | `wt_tour.airport_tax_price` + `wt_tour_price` (price_type=3) |
| **Waiver Of Charges** (price_type=4) | AduDiscAmt / Voucher / Credit Card Promo / Loyal Discount | number | `wt_tour_price` (price_type=4) |
| **Additional Discount** | [Add Custom Charge] | 动态 | 自定义 price_name |
| **Estimated Cost** ⚠️ | 9 个必填：Air Ticket / Airport Taxes / Land Tour Cost / Tour Leader Cost / Celebrity Cost / Referral Cost / Sales Commission(默认30) / Back Office Commission / Celebrity Commission | number /Pax | `wt_tour_estimated_cost` |
| **审计** | Created By, Adjusted By (readonly) | text | insert_time / update_user_id |
| 操作 | [Back] [Submit] | — | — |

**关键事实**：
- `SGLfare` = Single Room **总价**（含 supplement），不是 supplement 本身。`SGLfare - TWNfare = 单房差`
- `Estimated Cost` 区 9 个字段全部带 `*` 必填，v1 全填 0 即可（财务后续填）
- 航班 `seat_code` 默认 "G"，`flights_status` 默认 "RQ"
- `arrival_day` UI 显示 `0` / `+1`，DB 存 0 / 1

---

## Step 3 — Edit Display Detail（wt_travel + 子表）

URL: `editDisplayDetail?id=<wt_travel.id>&type=edit`

### 3.1 Basic Display Information

| 字段 | UI | wt_travel 字段 |
|---|---|---|
| Tour Type | readonly: `<type_code> | <type_name>` | tour_type_id (联动) |
| Product Name | 双语并排 textbox（左 EN / 右 CN） | `product_name` / `product_name_cn` |
| Highlight | 动态多行，每行双语并排 | `wt_travel_highlights` 多行 (highlights / highlights_cn) |
| List Thumbnail | 单图上传 | `list_thumbneil` (注意 schema 拼错 thumbnail) |
| Image Carousel | 最多 10 张 JPG/PNG，每张 ≤6MB，推荐 1920×1080 (16:9) | `wt_travel_image` (image_type=1 PC) |
| Cover Video Asset | 1 张 JPG/PNG，≤6MB，推荐 986×1752 (493:876 竖屏) | `video_cover_url` |
| Cover Video | 1 个 MP4，≤60s，≤50MB | `video_url` |
| Route Map | 单图上传 | `route_map_url` |

### 3.2 Sections（动态多个，对应 wt_travel_section）

UI 显示 `Section 1 - DAY 1` ~ `Section N - DAY N`，可折叠/展开/拖拽。

每个 Section 内部字段：

| 字段 | UI | wt_travel_section 字段 |
|---|---|---|
| Section Name | 双语并排 (e.g. `DAY 2` / `第二天`) | `section_name` / `section_name_cn` |
| Section Title | 双语并排 (e.g. `Quanzhou > Yongding`) | `section_title` / `section_title_cn` |
| Section Location | 双语并排 (e.g. `Yongding` / `永定`) | `section_location` / `section_location_cn` |
| Section Description | 双语并排 (e.g. `Breakfast / Lunch / Dinner` / `早餐 / 午餐 / 晚餐`) | `section_description` / `section_description_cn` |
| Image Grid | 最多 10 图 | `wt_travel_section_image` 多行 |
| Trip Item | [+ Add Trip Item] 按钮（**待 Phase 1 进一步探查具体结构**）| 待确认（可能拼接到 description，或另有表）|

按钮：[+ Add Section] / [Delete Section]

**sort_num 与 UI 对应**：
- UI 标签 "Section 1 - DAY 1" → DB 中 `sort_num` 实际值待 Phase 1 验证（Hokkaido 样本里 sort_num 0-7 对应 8 天，所以可能 DAY 1 = sort_num 0）

### 3.3 Dep Date & Price（聚合显示，readonly 表格）

显示该 wt_travel 关联的所有 wt_tour（通过 wt_travel_tour）的价格：

| 列 | 来源 |
|---|---|
| Dep Date | `wt_tour.departure_time` |
| Flight Info | `wt_tour.airline_code`（自动聚合显示如 "MF / CX"）|
| Tour Fare | `wt_tour_price.price_name`（如 "Adult Fare per pax[Twin Share]"）|
| Selling Price | `wt_tour_price.selling_price` |
| Cost Price | `wt_tour_price.cost_price` |
| Airport Tax | `wt_tour.airport_tax_price` |
| Qty | `wt_tour.inventory_num` |

**WBMXMN id=149 当前显示 "No Data"** —— 即使 RO DB 查到 6 个 wt_tour 关联到 tour_type_id=595，但它们**没通过 `wt_travel_tour` 关联到 travel_id=149**。

**结论**：插件 Step 3 必须显式写 `wt_travel_tour (travel_id, tour_type_id, tour_id)` 关联记录，否则前台显示"无出团"。

### 3.4 Product Status（发布开关）

| 字段 | UI | wt_travel.travel_status |
|---|---|---|
| Publish for sale | 复选框 | 不勾 = 0 (Not for sale, **草稿**)；勾 = 1 (publish for sale) |

**v1 规则**：插件**永不勾选**，永远留草稿态。Planner 在 Skybear 里手动勾。

### 3.5 操作

[Cancel] [Save]

---

## Step 1 — Tour Type（v1 不需要触碰）

WBMXMN 已存在 (id=595)，v1 范围**不创建新 TourType**。如未来需要，Tour Type 表单走 `Basic Information → Tour Type → Add New Record`，待 v2 探查。

---

## v1 Planner 输入 → UI 自动化映射（含字段默认值）

| Planner 在 Cowork 输入 | Step 2 Modal | Step 2 Edit page | Step 3 Edit Display Detail |
|---|---|---|---|
| 出发日期 2026-12-10 | Departure Date | (readonly) | (聚合显示) |
| 返程日期 2026-12-16（可推算）| Return Date | (readonly) | — |
| Travel Days 7（type 联动）| Travel Days | (readonly) | — |
| Tour Code `12WBMXMN10/26MF`（推导）| MM=12 + Type=WBMXMN + 后缀=10/26MF | (readonly) | — |
| 库存 30 | Quantity | (readonly) | — |
| 领队 "Marcus Chin" | TM/TL | (readonly) | — |
| 出境航班 MF886 SIN→XMN 0855-1315 | — | Flight Itinerary 行 1 | — |
| 返程航班 MF851 XMN→SIN 0940-1400 | — | Flight Itinerary 行 2 | — |
| Twin 价 2199 | — | Tour Fare TWNfare sellPrice | — |
| Single 总价（twin + supplement）| — | Tour Fare SGLfare sellPrice | — |
| 含床童价 2099 | — | Tour Fare ChdWEbed sellPrice | — |
| 不含床童价 1899 | — | Tour Fare ChdWOBed sellPrice | — |
| 机场税 250 | — | Additional Charges AirportTaxes/FuelSurcharge | — |
| Estimated Cost 9 项 | — | 全填 0 | — |
| PDF 提取 - Highlight 5-6 行双语 | — | — | Highlight 区 [+ Add] 多行 |
| PDF 提取 - 行程 7 天双语 | — | — | Section 1-7 (Section Name/Title/Location/Description) |
| PDF 提取 - 中英标题 | — | — | Product Name (双语) |
| 关联 tour_id 5985... → travel_id=149 | — | — | wt_travel_tour 关联（**Phase 1 确认 UI 路径**：可能在 Edit Display Detail 内有 "绑定 tour" 选项，或由后端自动按 tour_type_id 关联）|

**v1 不动的字段**：
- Image Carousel、Cover Video、List Thumbnail、Route Map（v1 不传图）
- Trip Item（先用 Section Description 拼景点列表）
- Land Tour、Waiver Of Charges、Additional Discount（留默认 0）
- Publish for sale（**永不勾**）

---

## 待 Phase 1 进一步探查

1. **Trip Item 内部结构** —— 点 `+ Add Trip Item` 看弹什么（是否有 trip_item_name / image / description 等？是另一张表还是 description 拼接？）
2. **Section 创建**：点 `+ Add Section` 后新 section 的 sort_num 怎么递增；DAY 1 的 sort_num 是 0 还是 1
3. **Modal "New Tour Code"** Tour Type 输入框的 autocomplete 行为（是 type_code 模糊匹配？还是必须完全匹配？）
4. **wt_travel_tour 关联**：Step 3 页面是否有显式 "绑定 tour" UI，还是后端自动按 tour_type_id 关联？目前 WBMXMN 的 tour 没绑过来，可能需要手动操作
5. **Modal `Save` 后跳转 URL 是新 wt_tour.id 还是有别的中间状态**（需要 Phase 1 实地走一遍）
6. **`Estimated Cost` 是否真的能全填 0 通过验证**（保险起见 Phase 1 用最小测试 tour 实测）
