# 安装 skybear-uploader

> 给 Webuy 内部 Planner / OP 看的安装文档。一次性配置，之后每次更新自动同步。

## 前置条件

- 已安装 Claude Cowork（macOS / Windows）
- Cowork 已登录公司账号
- Chrome 浏览器装好 [Claude in Chrome 扩展](https://claude.ai/chrome) 并登录

## 安装步骤（一次性）

1. **打开 Cowork**，进入聊天界面
2. **添加 marketplace**（粘贴下面这行到聊天框，回车）：

   ```
   /plugin marketplace add ctwang54-create/skybear-uploader
   ```

   > 私有 repo 需要先在 Cowork 设置里授权 GitHub 账号（Settings → Integrations → GitHub）。
   > 同事必须先被加为 repo collaborator 才能 clone：
   > `gh repo add-collaborator ctwang54-create/skybear-uploader <他的-github-用户名>`

3. **安装 plugin**：

   ```
   /plugin install skybear-uploader@webuy-skybear
   ```

4. **验证安装**：聊天里输入 `/plugin list`，应该看到 `skybear-uploader`。

## 日常使用

直接拖一份 PDF 进 Cowork 聊天，说类似：

> 把这个上架到 Skybear test 环境

然后按聊天提示回答 7 个问题（出发日期、航班、价格等）→ 确认 → Claude 自动驱动 Chrome 完成 Skybear 录入 → 你在 Skybear 上手动点 **Publish for sale**。

## 升级

```
/plugin update skybear-uploader
```

每次开发者 push 新版本，运行这条命令同步即可。

## 故障排查

| 现象 | 解决 |
|---|---|
| `Unknown skill: ...` | 用 `/plugin install`，不是输入文件路径 |
| `Permission denied` 装 marketplace | 需要先在 Cowork → Settings → Integrations 里连 GitHub 账号 |
| Chrome 没连上 | 装 Claude in Chrome 扩展并登录 claude.ai |
| Skybear 登录失败 | 在自己 Chrome 里手动登录 https://test01.travel.webuy.ren，再回 Cowork 重试 |

## 联系开发者

[wangchengtai] / 内部 Wiki: <填上> / Slack 频道: <填上>
