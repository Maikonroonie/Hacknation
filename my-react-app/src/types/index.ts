export interface MasterRecord {
  Date: string;
  PKD_Code: string;
  Revenue: string;
  Profit: string;
  Bankruptcy_Rate: string;
  PKO_SCORE: string;
  PKO_SCORE_FINAL: string;
  Rank_Growth?: number;
  Rank_Slowdown?: number;
  Rank_Loan_Needs?: number;
  Rank_Trend_Signal?: number;
  }

export interface PredictionRecord {
  Date: string;
  PKD_Code: string;
  Predicted_Score: string;
  Confidence_Lower: string;
  Confidence_Upper: string;
  Rank_Growth_Predicted?: number;
  Rank_Slowdown_Predicted?: number;
  Rank_Loan_Needs_Predicted?: number;
  Rank_Trend_Signal_Predicted?: number;
}

// TEGO BRAKOWAŁO:
export interface IndustrySummary {
  pkdCode: string;
  pkdName: string; 
  currentScore: number;
  revenue: number;
}