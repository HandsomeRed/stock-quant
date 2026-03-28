# Stage 4 实盘对接方案（低门槛版）

**更新日期：** 2026-03-28  
**决策：** 放弃 30w 资金券商 API 方案，改用聚宽/QMT 低门槛路线

---

## 🎯 三阶段实盘路线

### Phase 1: 聚宽 JoinQuant 模拟交易（立即开始）
**门槛：** 免费注册，无资金要求  
**目标：** 在聚宽平台验证策略有效性

**接入方式：**
1. 注册聚宽账号（joinquant.com）
2. 使用聚宽 Jupyter 研究环境
3. 迁移现有策略到聚宽 API
4. 开启模拟交易

**聚宽 API 特点：**
```python
# 聚宽策略模板
def initialize(context):
    set_benchmark('000300.XSHG')
    run_daily(trade, '9:30')

def trade(context):
    # 获取股票数据
    df = get_price('000001.XSHE', start_date='2024-01-01')
    # 交易逻辑
    order_target('000001.XSHE', 100)
```

**优势：**
- ✅ 免费使用
- ✅ 数据齐全（A 股/基金/期货）
- ✅ 支持模拟交易
- ✅ 社区策略丰富

---

### Phase 2: 聚宽实盘对接（3-6 个月后）
**门槛：** 通过聚宽对接合作券商  
**目标：** 小资金实盘验证

**支持券商：** 部分支持聚宽实盘的券商（需调研具体名单）

---

### Phase 3: QMT/Ptrade 本地实盘（6-12 个月）
**门槛：** 1-5w 资金（部分券商）  
**目标：** 完全自主控制的量化交易

**支持 QMT 的券商：**
- 国金证券
- 华宝证券
- 银河证券
- 其他...（需调研）

**QMT 特点：**
- Python 策略本地运行
- 直接对接券商交易接口
- 低延迟
- 支持条件单、网格交易

---

## 📋 下一步行动

### 本周任务
1. [ ] 注册聚宽账号
2. [ ] 阅读聚宽 API 文档
3. [ ] 迁移 RSI 策略到聚宽平台
4. [ ] 开启模拟交易测试

### 策略迁移清单
- [x] Stage 1 数据获取（AKShare → 聚宽 get_price）
- [ ] Stage 1b 技术指标（TA-Lib → 聚宽指标函数）
- [ ] Stage 2 回测引擎（本地 → 聚宽回测）
- [ ] Stage 3 模拟交易（本地模拟 → 聚宽模拟盘）
- [ ] Stage 3b 策略库（RSI/布林带/MACD/放量突破）

---

## 🔗 参考资源

- 聚宽官网：https://www.joinquant.com
- 聚宽 API 文档：https://www.joinquant.com/help/api/help
- 聚宽社区策略：https://www.joinquant.com/algorithm
- QMT 官方文档：https://www.myquant.cn

---

**状态：** 🔄 Phase 1 准备中
