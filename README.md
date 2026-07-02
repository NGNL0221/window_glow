# WindowGlow

🪟 Windows 焦点窗口发光边框 — 为当前活动窗口添加青色→蓝紫渐变发光光晕。

## ✨ 功能

- 🔍 自动追踪焦点窗口，实时跟随移动
- 🌈 青色 → 蓝紫色渐变边框，顺滑余弦边缘
- 💨 可选的呼吸动画（`config.json` 开启）
- 🖱️ 系统托盘图标，后台静默运行
- ⌨️ `Alt + B` 全局快捷键切换
- 🎨 圆角发光，向外自然衰减

## 🚀 使用方式

1. 下载本仓库所有文件
2. 确保已安装 **Python 3.8+**（零外部依赖）
3. 双击 `WindowGlow.pyw` 启动（无控制台窗口）
4. 右下角托盘图标：
   - **左键单击** — 开关灯带
   - **右键** — 弹出菜单（Toggle Glow / Exit）

## ⚙️ 配置

编辑 `window_glow/config.json`：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `border_width` | 15 | 边框粗细（像素） |
| `color.start_hue` | 180 | 起始色相（0=红, 180=青） |
| `color.end_hue` | 270 | 终止色相（270=蓝紫） |
| `animation.enabled` | false | 呼吸动画开关 |
| `animation.speed` | 0.8 | 呼吸速度（越大越快） |

## 📋 要求

- Windows 10 / 11
- Python 3.8+
- 零外部依赖（仅标准库 `ctypes`）

## 📄 License

MIT
