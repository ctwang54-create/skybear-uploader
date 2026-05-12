# 安装 skybear-uploader

> 给 Webuy Planner / OP 看的安装文档。**默认上传到生产环境 `travel.webuysg.com`**。
> 一次性配置，之后每次开 Cowork 直接用。

## 前置条件

- Claude Cowork 桌面 app（macOS / Windows）已装好并登录公司账号
- Google Chrome 浏览器
- 你有 **prod Skybear 后台**（`https://travel.webuysg.com`）的登录账号

> Planner **不需要**装 Python / 配 .env / 装数据库凭据。Plugin 自带的 Python 库是开发者工具，日常使用走 Chrome UI。

## 一次性设置

### 1. 接受 GitHub repo 邀请

打开邀请邮件里的链接，或直接访问：

**https://github.com/ctwang54-create/skybear-uploader/invitations**

登录你的 GitHub 账号后点 **Accept invitation**。

### 2. 装 Claude in Chrome 扩展

打开 Chrome → 访问 **https://claude.ai/chrome** → Install。
装好后在 Chrome 里登一次 claude.ai。

### 3. 在 Cowork 里装 plugin

打开 Cowork，在聊天框依次粘贴这两条命令（一次一条，回车）：

```
/plugin marketplace add ctwang54-create/skybear-uploader
```

> ⚠️ 报 `GitHub authorization required` → 去 **Cowork → Settings → Integrations → Connect GitHub** 绑定你的 GitHub 账号，回来再跑。

```
/plugin install skybear-uploader@webuy-skybear
```

验证：输入 `/plugin list`，看到 `skybear-uploader` 即成功。

### 4. 登录 prod Skybear

在你 Chrome 里打开 **https://travel.webuysg.com** 用自己的账号登入。
**这个 tab 保持登录状态**，不要登出 / 不要清 cookie。

---

## 上架一个行程

### Step 1 — 拖 PDF + 触发

把行程 PDF 文件拖入 Cowork 聊天框，并发一句：

> 把这个上架到 Skybear

按回车。

### Step 2 — 选环境

Plugin 第一句话会问：

> **Upload to which environment?**
> - Production — https://travel.webuysg.com (推荐)
> - UAT test — https://test01.travel.webuy.ren

选 **Production**。（如果开发或测试请选 UAT）

### Step 3 — 等 PDF 提取

约 60 秒，Plugin 会读 PDF 内容并显示提取的双语标题 / 亮点 / Day 1-N 行程结构。

### Step 4 — 回答 7 个问题

Plugin 会问你下面几项。可以一次性贴答（每行一条）：

```
1. 出发日期：2026-12-10
2. 航司代码：MF
3. 出境航班：MF886 SIN-XMN 0855-1315
4. 返程航班：MF851 XMN-SIN 0940-1400
5. 领队：Marcus Chin
6. 库存：30
7. Twin 价：2199；机场税：250
```

价格**只输入 Twin 一个数**，其他档位 Plugin 自动算：
- TRPFare / ChdHfTwn = Twin (2199)
- ChdWEbed = Twin − 40 (2159)
- ChdWOBed = Twin − 100 (2099)
- SGLfare = Twin + 400 (2599)

### Step 5 — 确认 review

Plugin 显示一份总结（type code / tour code / 价格 / 草稿状态）。
输入 `OK` 或 `继续` 确认。

### Step 6 — 看 Chrome 自动操作

约 3 分钟。Plugin 会驱动你的 Chrome 自动：
1. 在 Skybear 创建新 Tour Code
2. 填价格 / 填航班 / 填 Estimated Cost
3. 点 Submit
4. 进 Package Content Mgmt 勾选绑定 + Save

你不需要动手，看着它跑就行。

### Step 7 — 手动 Publish ⚠️ 你必须做的最后一步

Plugin 完成后给你两个 URL。请按顺序：

1. **打开第一个 URL**（Edit Package 页）：
   - 补 **TM/TL** 字段：填领队名（例如 `Marcus Chin`）
   - 补 **Main Airline** 字段：填航司（例如 `MF`）
   - 点 **Submit**
2. **打开第二个 URL**（Edit Display Detail 页）：
   - 拉到底部，勾选 ✅ **Publish for sale**
   - 点 **Save**

完成 5-10 分钟后产品上线 **https://www.webuytravel.sg/**。

---

## 升级

开发者推新版后：

```
/plugin update skybear-uploader
```

---

## 出问题怎么办

| 现象 | 处理 |
|---|---|
| 拖 PDF 没反应 | 加一句 "上架到 Skybear" 明确触发 |
| Chrome 没连上 | 装 Claude in Chrome 扩展并登 claude.ai |
| Skybear 登不上 | 自己 Chrome 手动登一次 `https://travel.webuysg.com`，再回 Cowork 继续 |
| Plugin 卡半路 | 截图聊天给开发者 wangchengtai |
| 创建后想撤 | Skybear UI 点 Modify → 改 Tr Status 为 Canceled |

## 联系开发者

wangchengtai · GitHub @ctwang54-create
