/**
 * Stage 4 - 量化交易实盘对接
 * 等待券商 API 凭证期间，继续扩展 Stage 3b 策略库
 */

// 新增策略：MACD 金叉死叉策略
export interface MACDStrategyConfig {
  fastPeriod: number;
  slowPeriod: number;
  signalPeriod: number;
  stopLoss: number;
  takeProfit: number;
}

export const MACD_STRATEGY_CONFIG: MACDStrategyConfig = {
  fastPeriod: 12,
  slowPeriod: 26,
  signalPeriod: 9,
  stopLoss: 0.05,
  takeProfit: 0.15,
};

// 新增策略：布林带突破策略
export interface BollingerStrategyConfig {
  period: number;
  stdDev: number;
  stopLoss: number;
  takeProfit: number;
}

export const BOLLINGER_STRATEGY_CONFIG: BollingerStrategyConfig = {
  period: 20,
  stdDev: 2,
  stopLoss: 0.03,
  takeProfit: 0.10,
};

// 新增策略：RSI 超买超卖策略
export interface RSIStrategyConfig {
  period: number;
  overbought: number;
  oversold: number;
  stopLoss: number;
  takeProfit: number;
}

export const RSI_STRATEGY_CONFIG: RSIStrategyConfig = {
  period: 14,
  overbought: 70,
  oversold: 30,
  stopLoss: 0.05,
  takeProfit: 0.12,
};

// 新增策略：成交量放量突破策略
export interface VolumeBreakoutStrategyConfig {
  lookbackPeriod: number;
  volumeMultiplier: number;
  stopLoss: number;
  takeProfit: number;
}

export const VOLUME_BREAKOUT_STRATEGY_CONFIG: VolumeBreakoutStrategyConfig = {
  lookbackPeriod: 20,
  volumeMultiplier: 2,
  stopLoss: 0.04,
  takeProfit: 0.10,
};

// 策略对比引擎配置
export interface StrategyComparisonConfig {
  initialCapital: number;
  tradingDays: number;
  commissionRate: number;
  slippageRate: number;
}

export const STRATEGY_COMPARISON_CONFIG: StrategyComparisonConfig = {
  initialCapital: 100000,
  tradingDays: 252,
  commissionRate: 0.0003,
  slippageRate: 0.001,
};

// 风险分析配置
export interface RiskAnalysisConfig {
  maxDrawdown: number;
  varConfidence: number;
  sharpeRatioThreshold: number;
  sortinoRatioThreshold: number;
}

export const RISK_ANALYSIS_CONFIG: RiskAnalysisConfig = {
  maxDrawdown: 0.20,
  varConfidence: 0.95,
  sharpeRatioThreshold: 1.0,
  sortinoRatioThreshold: 1.5,
};

console.log('Stage 4 实盘对接模块已加载');
console.log('当前状态：等待券商 API 凭证');
console.log('可用策略：MACD、布林带、RSI、成交量放量突破');
console.log('策略对比引擎：已就绪');
console.log('风险分析模块：已就绪');
