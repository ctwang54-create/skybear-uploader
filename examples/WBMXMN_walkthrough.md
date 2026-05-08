# Sample Cowork session — WBMXMN 12月期上架

> 这是一份样例对话，展示 Planner 用 `skybear-uploader` 插件把 `WBMXMN.pdf`
> 12 月 10 日出团那一期上架到 Skybear UAT 的全流程。

---

**Planner**: *拖入 `WBMXMN - PRESENTED BY BUKIT PANJANG KHEK COMMUNITY GUILD · TRAVEL WITH MARCUS CHIN.pdf` (38MB, 4 pages)*
帮我把这个配套上架到 skybear test 环境。

**Claude** *(invokes `skybear-upload-package`)*: 收到。我先读 PDF。

> *PDF > 20MB → 先用 PyMuPDF 渲染每页为 1600px PNG，存到 /tmp/wbmxmn_pages/*

PDF 提取完成（4 页），我抽出来的字段：

```yaml
tour_type:
  type_code: WBMXMN
  type_name_en: "7D6N HAKKA HOMELAND × MINNAN CULTURAL DISCOVERY — TRAVEL WITH MARCUS CHIN"
  type_name_cn: "7天6晚穿越客家原乡 × 闽南文化深度之旅 — 与陈建彬同行"
  travel_days: 7

departure_date_hint: 2026-12-10

travel:
  product_name_en: <同 type_name_en>
  product_name_cn: <同 type_name_cn>
  cities_cn: ["厦门", "泉州", "永定", "大埔", "梅州", "汕头", "潮州"]
  meal_plan_summary: "6 Breakfasts / 6 Lunches / 6 Dinners"
  accommodation_level: "Local 5 Star Hotel / 全程当地 5 星"
  highlights:
    - { en: "Celebrity-led experience",
        cn: "明星陪团，全程互动体验" }
    - { en: "UNESCO Heritage: Hongkeng Tulou & Gulangyu Island",
        cn: "世界遗产 ✦ 洪坑土楼 ✦ 鼓浪屿" }
    - { en: "Hakka culture hands-on (DIY rice cake)",
        cn: "客家文化深度体验 - DIY 粄粄 + 博物馆" }
    - { en: "Intangible heritage: Yingge Dance & floral hairpin",
        cn: "非遗文化体验 - 英歌舞 + 簪嫔围" }
    - { en: "10 Signature Cuisines incl. Black Pearl dining",
        cn: "10 大特色美食 - 黑珍珠雅宴 + 潮汕菜" }
  sections:
    - sort_num: 0  # DAY 1
      title_en: "SINGAPORE → XIAMEN → 1.5H QUANZHOU"
      title_cn: "新加坡 → 厦门 → 1.5h 泉州"
      location_en: "Quanzhou"
      location_cn: "泉州"
      description_en: "Lunch / Dinner. Wudianshi Traditional Culture District."
      description_cn: "中餐 / 晚餐。五店市传统文化街区。"
    # ... DAY 2-7
```

PDF 没有的信息我需要你提供：
1. 出发日期（PDF 显示 2026-12-10，确认？）
2. 航司代码（例如 MF）
3. 出境航班（例如 `MF886 SIN-XMN 0855-1315`）
4. 返程航班（例如 `MF851 XMN-SIN 0940-1400`）
5. 领队姓名
6. 库存数
7. Twin 价（v1 默认公式：SGL=Twin+400, ChdW/Bed=Twin-40, ChdW/o=Twin-100）
8. 机场税

---

**Planner**:
```
1. 是 2026-12-10
2. MF
3. MF886 SIN-XMN 0855-1315
4. MF851 XMN-SIN 0940-1400
5. Marcus Chin
6. 30
7. Twin 2199
8. 机场税 250
```

**Claude**: 好。我推算返程日期 = 2026-12-16（出发 + 6 晚）。Tour code 推导:
`12` (出发月) + `WBMXMN` + `10/26MF` (DD/YY+航司) → **`12WBMXMN10/26MF`**.

价格按默认公式：
- TWN / TRP / ChdHfTwn = 2199
- ChdWEbed = 2159
- ChdWOBed = 2099
- SGLfare = 2599
- Infant = 0
- Airport Tax = 250

我去查 UAT MySQL slave 看现状...

> *运行 `lib.existence_check.check(settings, "WBMXMN", "12WBMXMN10/26MF")`*

| | 状态 | id | 备注 |
|---|---|---|---|
| Tour Type | **REUSE** | 595 | pax_type=1 ✓, area_id=337, travel_days=7 |
| Tour Code | **NEW** | — | 12WBMXMN10/26MF 还不存在 |
| wt_travel | **REUSE** | 149 | 草稿态；Section 1-7 + Highlight 已填 |

最终方案：
- ✅ 不创建新 TourType（复用 WBMXMN id=595）
- ✅ 在 Skybear 创建新 wt_tour `12WBMXMN10/26MF`（Step 2）
- ✅ 在 wt_travel id=149 上**只增加 wt_travel_tour 关联**（绑定新 tour_id），不改其他字段（Step 3）
- ✅ 不勾 "Publish for sale"（保持草稿）

确认开始吗？输入 `OK` / `继续` 即开干。

---

**Planner**: OK 继续

**Claude** *(delegates to `skybear-create-tourcode`)*:

> *打开 Chrome 到 `https://test01.travel.webuy.ren`*
> *如已登录: 跳过；否则提示 Planner 在浏览器登录*

Step 2.1 — Modal "New Tour Code"：
- MM 下拉 → `12`
- Tour Type autocomplete → 输 `WBMXMN`，等联动加载 type_name + Region + Pax Type
- 后缀 → `10/26MF`
- Tour Name → 自动从 type_name 拉，保留
- Departure Date → `10/12/2026` (DD/MM/YYYY)
- Travel Days → `7`
- Return Date → `16/12/2026`
- Quantity → `30`
- Paym Due Days → 留默认 21
- TM/TL → `Marcus Chin`
- 点 [Save]

Modal 关闭，URL 跳到 `editPackage?id=NNNN&type=edit`（拿到新 tour_id = NNNN）。

Step 2.2 — Edit Package 页：
- Tr Status → `Pending` (默认即草稿)
- Flight Itinerary 行 1: `10/12/2026 / MF886 / SIN / XMN / 0855 / 1315 / 0 / G / RQ`
- Flight Itinerary 行 2: `16/12/2026 / MF851 / XMN / SIN / 0940 / 1400 / 0 / G / RQ`
- Tour Fare:
  - SGLfare.sellPrice = 2599
  - TWNfare.sellPrice = 2199
  - TRPFare.sellPrice = 2199
  - ChdHfTwn.sellPrice = 2199
  - ChdWEbed.sellPrice = 2159
  - ChdWOBed.sellPrice = 2099
  - InfFare.sellPrice = 0
- Land Tour: 全留 0
- Additional Charges: AirportTaxes/FuelSurcharge = 250
- Waiver / Discount: 全留 0
- Estimated Cost (9 必填): 全填 0（Sales Commission 用默认 30）
- 点 [Submit]

✅ Step 2 完成 — `12WBMXMN10/26MF` (id=NNNN) 已创建，Tr Status = Pending (草稿)。

---

**Claude** *(delegates to `skybear-update-display`)*:

Step 3 — Edit Display Detail (wt_travel id=149)：
- 因 wt_travel id=149 已经填好了 Section 1-7 + Highlight + Product Name
- v1 只做 wt_travel_tour 绑定（让新 tour_id 出现在 Dep Date & Price 表里）
- **Publish for sale 复选框：保持不勾**
- 点 [Save]

✅ Step 3 完成 — 新 tour_id 已绑定到 wt_travel id=149。

---

**Claude** *(delegates to `skybear-verify`)*:

> *打开 https://www.webuytravel.sg 搜 "陈建彬" / "WBMXMN" / "Hakka Homeland"*

公开站搜索结果：
- 草稿态产品**不会**显示在公开站（实测：搜 "WBMXMN" → 0 results）
- 待 Planner 在 Skybear 上勾 `Publish for sale` 后，约 2-5 分钟内会出现在 webuytravel.sg

---

最终报告：

```
TourType:    WBMXMN id=595        REUSED
TourCode:    12WBMXMN10/26MF      CREATED  id=NNNN  status=Pending(draft)
wt_travel:   id=149                REUSED   bound new tour
Public site: not visible (expected — draft)

下一步（手动）：
  1. 进 Skybear → Package List → 找 12WBMXMN10/26MF → 复核
  2. 进 Package Content Mgmt → WBMXMN → 勾 "Publish for sale" → Save
  3. 等 5 分钟，去 webuytravel.sg 确认上架
```

**Planner**: 👍 收到，我去 publish。
