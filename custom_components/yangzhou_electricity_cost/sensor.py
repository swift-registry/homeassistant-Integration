import logging
from datetime import datetime, date
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# --- 配置区域 ---
DOMAIN = "yangzhou_electricity_cost"
DEFAULT_NAME = "扬州预估电费"
# ⚠️ 这里填入你的电表实体ID
SOURCE_SENSOR_ID = "sensor.zhi_neng_dian_biao_dian_li" 

# --- 电价参数 (江苏/扬州标准) ---
PRICE_PEAK = 0.5583   # 峰段电价 (8:00-21:00)
PRICE_VALLEY = 0.3583 # 谷段电价 (21:00-次日8:00)
TIER_2_ADD = 0.05     # 第二档加价
TIER_3_ADD = 0.30     # 第三档加价

# 阶梯阈值 (按年累计)
YEARLY_TIER_1_LIMIT = 2760
YEARLY_TIER_2_LIMIT = 4800

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType = None,
):
    """设置平台"""
    async_add_entities([YangzhouCostSensor()])


class YangzhouCostSensor(SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:cash-multiple"
    _attr_unit_of_measurement = "元"

    def __init__(self):
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = "yangzhou_estimated_cost_v1"
        
    @property
    def extra_state_attributes(self):
        """返回一些额外的属性，方便你在仪表盘查看细节"""
        return {
            "源传感器": SOURCE_SENSOR_ID,
            "当前总电量(kWh)": self._current_total_kwh,
            "预估峰段占比": "65% (估算)",
            "当前月份": f"{datetime.now().month}月",
            "说明": "基于总电量估算，未区分实际峰谷读数"
        }

    async def async_added_to_hass(self):
        """当实体添加到HA时，监听源传感器的变化"""
        self.async_on_remove(
            self.hass.states.async_track_state_change_event(
                [SOURCE_SENSOR_ID], self._async_update_callback
            )
        )
        # 初始化时计算一次
        self._update_cost()

    async def _async_update_callback(self, event):
        """回调函数：当电表读数变化时触发"""
        self._update_cost()

    def _update_cost(self):
        """核心计算逻辑"""
        state = self.hass.states.get(SOURCE_SENSOR_ID)
        
        if state is None or state.state in ["unknown", "unavailable"]:
            _LOGGER.warning(f"无法获取传感器 {SOURCE_SENSOR_ID} 的状态")
            return

        try:
            total_kwh = float(state.state)
            self._current_total_kwh = total_kwh
            
            # 1. 估算峰谷电量 (因为没有单独的历史数据，只能按比例估算)
            # 夏季空调多，假设峰段占 65%，谷段 35%
            peak_kwh = total_kwh * 0.65
            valley_kwh = total_kwh * 0.35
            
            base_cost = (peak_kwh * PRICE_PEAK) + (valley_kwh * PRICE_VALLEY)
            
            # 2. 计算阶梯加价 (按当前月份推算年度额度)
            current_month = datetime.now().month
            # 每月平均额度
            monthly_tier1 = YEARLY_TIER_1_LIMIT / 12
            monthly_tier2_limit = YEARLY_TIER_2_LIMIT / 12
            
            # 截止当前的年度总额度
            current_year_tier1_cap = monthly_tier1 * current_month
            current_year_tier2_cap = monthly_tier2_limit * current_month
            
            tier_surcharge = 0.0
            
            if total_kwh > current_year_tier2_cap:
                # 进入第三档
                # 简化算法：超出部分全部算第三档 (实际上应该分段，但为了估算这样误差可接受)
                tier_surcharge += (total_kwh - current_year_tier2_cap) * TIER_3_ADD
                # 补算第二档满额部分的加价
                tier_surcharge += (current_year_tier2_cap - current_year_tier1_cap) * TIER_2_ADD
                
            elif total_kwh > current_year_tier1_cap:
                # 进入第二档
                tier_surcharge += (total_kwh - current_year_tier1_cap) * TIER_2_ADD
            
            final_cost = base_cost + tier_surcharge
            
            self._attr_native_value = round(final_cost, 2)
            self.schedule_update_ha_state()
            
        except ValueError:
            _LOGGER.error(f"传感器数值转换错误: {state.state}")

    async def async_update(self):
        pass