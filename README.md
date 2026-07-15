# 扬州电费预估 (Yangzhou Electricity Cost)

这是一个专为 Home Assistant 设计的自定义组件，用于实时预估扬州市居民阶梯+峰谷分时电费。

## ✨ 功能特点
- **精准计算**：内置江苏/扬州居民峰谷电价标准（峰段 0.5583元，谷段 0.3583元）。
- **智能阶梯**：根据当前月份自动推算年度阶梯额度，超出部分自动叠加二档/三档加价。
- **低资源消耗**：仅在电表读数发生变化时触发计算，不占用额外系统资源。

## 📦 安装步骤

### 方法一：通过 HACS 安装（推荐）
1. 在 HACS 中点击 `Integrations` -> 右上角菜单 -> `Custom repositories`。
2. 填入本仓库的 GitHub 链接，Category 选择 `Integration`。
3. 搜索 `Yangzhou Electricity Cost` 并下载安装。
4. 重启 Home Assistant。

### 方法二：手动安装
1. 下载本仓库代码，将 `custom_components/yangzhou_electricity_cost` 文件夹复制到你的 HA 配置目录中。
2. 重启 Home Assistant。

## ⚙️ 配置说明
由于目前 HA 的 Template 传感器无法直接读取历史峰谷电量，本插件默认采用 **65% 峰段 / 35% 谷段** 的比例进行估算。

如需修改源电表实体，请编辑 `custom_components/yangzhou_electricity_cost/sensor.py` 文件中的以下变量：
```python
SOURCE_SENSOR_ID = "sensor.zhi_neng_dian_biao_dian_li" # 替换为你的电表实体ID