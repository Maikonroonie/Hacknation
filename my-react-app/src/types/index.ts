export interface MasterRecord {
  Date: string;
  PKD_Code: string;
  Revenue: string;
  Profit: string;
  Bankruptcy_Rate: string;
  PKO_SCORE: string;
  PKO_SCORE_FINAL: string;
}

export interface PredictionRecord {
  Date: string;
  PKD_Code: string;
  Predicted_Score: string;
  Confidence_Lower: string;
  Confidence_Upper: string;
}

// TEGO BRAKOWAŁO:
export interface IndustrySummary {
  pkdCode: string;
  pkdName: string; 
  currentScore: number;
  revenue: number;
}