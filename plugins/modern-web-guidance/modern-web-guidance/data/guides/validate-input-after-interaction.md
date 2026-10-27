# 用户交互后再显示表单错误

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[validate-input-after-interaction](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/forms/validate-input-after-interaction.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

通过 `required`、`type="email"`、`pattern` 等原生约束表达校验条件，再用 `:user-invalid` 延后显示错误。不要使用初始 `:invalid` 状态把尚未填写的字段全部标红。

```html
<form>
  <label for="email">电子邮箱</label>
  <p id="email-hint">例如 user@example.com</p>
  <input id="email" name="email" type="email" required autocomplete="email"
         aria-describedby="email-hint" aria-errormessage="email-error">
  <span id="email-error" class="error-msg">请输入有效的电子邮箱。</span>
  <button type="submit">提交</button>
</form>
```

```css
.error-msg { display: none; }
/* 与降级规则分开，避免不认识选择器的浏览器丢弃整组规则。 */
input.user-invalid-fallback { border-color: #b00020; }
input.user-invalid-fallback + .error-msg { display: inline; }
@supports selector(:user-invalid) {
  input:user-invalid { border-color: #b00020; }
  input:user-invalid + .error-msg { display: inline; }
}
```

兼容与降级：上游记录 `:user-valid` / `:user-invalid` 自 2023-11-02 达到 Baseline，列出 Chrome/Edge 119、Firefox 88、Safari 16.5。旧浏览器需跟踪已交互/失焦状态，用 `validity.valid` 更新类；提交失败后要显示相关错误，重置时清除状态。尽量保留原生表单提交及校验路径。

CSS 状态不会自动同步 `aria-invalid`。对表单控件同步该属性，并保持文字提示与视觉状态一致；首次渲染不强制宣布错误。支持检测通过后才调用 `matches(':user-invalid')`。必要的格式提示放在输入框上方，避免被自动填充浮层遮挡。

检查：初次显示、输入中、失焦、提交失败、纠正以及重置。客户端校验不能取代服务器验证；密码规则必须遵循项目要求，不能从示例直接引入任意复杂度策略。
