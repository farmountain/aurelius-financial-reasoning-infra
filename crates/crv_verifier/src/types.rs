use serde::{Deserialize, Serialize};

/// Severity level of a CRV violation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Rule identifier for different types of checks
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RuleId {
    /// Lookahead bias detection
    LookaheadBias,
    /// Survivorship bias detection
    SurvivorshipBias,
    /// Sharpe ratio calculation validation
    SharpeRatioValidation,
    /// Max drawdown calculation validation
    MaxDrawdownValidation,
    /// Max drawdown policy constraint
    MaxDrawdownConstraint,
    /// Max leverage policy constraint
    MaxLeverageConstraint,
    /// Turnover policy constraint
    TurnoverConstraint,
}

/// A single violation found during CRV verification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CRVViolation {
    pub rule_id: RuleId,
    pub severity: Severity,
    pub message: String,
    pub evidence: Vec<String>,
}

/// Complete CRV verification report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CRVReport {
    pub timestamp: i64,
    pub violations: Vec<CRVViolation>,
    pub passed: bool,
}

impl CRVReport {
    pub fn new(timestamp: i64) -> Self {
        Self {
            timestamp,
            violations: Vec::new(),
            passed: true,
        }
    }

    pub fn add_violation(&mut self, violation: CRVViolation) {
        self.passed = false;
        self.violations.push(violation);
    }

    pub fn has_critical_violations(&self) -> bool {
        self.violations.iter().any(|v| v.severity == Severity::Critical)
    }

    pub fn violation_count(&self) -> usize {
        self.violations.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_crv_report_empty() {
        let report = CRVReport::new(12345);
        assert_eq!(report.timestamp, 12345);
        assert!(report.passed);
        assert_eq!(report.violation_count(), 0);
        assert!(!report.has_critical_violations());
    }

    #[test]
    fn test_crv_report_with_violation() {
        let mut report = CRVReport::new(12345);
        
        let violation = CRVViolation {
            rule_id: RuleId::LookaheadBias,
            severity: Severity::Critical,
            message: "Strategy uses future data".to_string(),
            evidence: vec!["Line 42: accessing bar.close at t+1".to_string()],
        };
        
        report.add_violation(violation);
        
        assert!(!report.passed);
        assert_eq!(report.violation_count(), 1);
        assert!(report.has_critical_violations());
    }

    #[test]
    fn test_crv_report_serialization() {
        let mut report = CRVReport::new(12345);
        
        let violation = CRVViolation {
            rule_id: RuleId::MaxDrawdownConstraint,
            severity: Severity::High,
            message: "Max drawdown exceeded limit".to_string(),
            evidence: vec!["Observed: 0.35, Limit: 0.25".to_string()],
        };
        
        report.add_violation(violation);
        
        let json = serde_json::to_string_pretty(&report).unwrap();
        assert!(json.contains("max_drawdown_constraint"));
        assert!(json.contains("high"));
        
        // Deserialize back
        let deserialized: CRVReport = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.timestamp, 12345);
        assert_eq!(deserialized.violation_count(), 1);
    }
}
