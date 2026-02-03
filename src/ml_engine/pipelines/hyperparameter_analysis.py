"""
PHASE 5.6: COMPREHENSIVE HYPERPARAMETER ANALYSIS
================================================
Hyperparameter sensitivity and optimization analysis:
- Sensitivity analysis (parameter impact)
- Generalization gap analysis
- Parameter importance ranking
- Hyperparameter optimization suggestions
- Learning dynamics analysis

Status: PRODUCTION READY
Lines: 650+ core implementation
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional, Callable
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

log = logging.getLogger(__name__)


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================

class SensitivityAnalysis:
    """Analyze sensitivity of model to hyperparameter changes."""

    def __init__(self):
        """Initialize sensitivity analysis."""
        self.results = {}

        log.info("✅ SensitivityAnalysis initialized")

    def analyze_parameter_impact(self, param_name: str, param_values: List[Any],
                                 scores: List[float]) -> Dict[str, Any]:
        """
        Analyze impact of parameter on model performance.

        Args:
            param_name: Name of hyperparameter
            param_values: List of parameter values tested
            scores: Corresponding model scores

        Returns:
            Dictionary with sensitivity metrics
        """
        param_values = np.array(param_values)
        scores = np.array(scores)

        # Calculate sensitivity metrics
        score_range = np.max(scores) - np.min(scores)
        score_mean = np.mean(scores)
        score_std = np.std(scores)

        # Correlation with parameter
        if len(param_values) > 1:
            # Convert to numeric if possible
            try:
                param_numeric = np.array([float(p) for p in param_values])
                correlation = np.corrcoef(param_numeric, scores)[0, 1]
            except:
                correlation = np.nan
        else:
            correlation = np.nan

        # Find optimal value
        optimal_idx = np.argmax(scores)
        optimal_param = param_values[optimal_idx]
        optimal_score = scores[optimal_idx]

        log.info("=" * 80)
        log.info(f"📊 SENSITIVITY ANALYSIS: {param_name}")
        log.info("=" * 80)
        log.info(f"  Score Range: {score_range:.4f}")
        log.info(f"  Score Mean: {score_mean:.4f}")
        log.info(f"  Score Std: {score_std:.4f}")
        log.info(f"  Correlation: {correlation:.4f}")
        log.info(f"  Optimal Value: {optimal_param}")
        log.info(f"  Best Score: {optimal_score:.4f}")
        log.info("=" * 80)

        result = {
            'parameter': param_name,
            'values_tested': len(param_values),
            'score_range': float(score_range),
            'score_mean': float(score_mean),
            'score_std': float(score_std),
            'correlation': float(correlation) if not np.isnan(correlation) else None,
            'optimal_value': optimal_param,
            'optimal_score': float(optimal_score),
            'sensitivity': float(score_range / score_mean) if score_mean != 0 else 0
        }

        self.results[param_name] = result

        return result

    def compare_parameters(self) -> pd.DataFrame:
        """Compare sensitivity across all analyzed parameters."""
        if not self.results:
            log.warning("No sensitivity analysis results available")
            return pd.DataFrame()

        df = pd.DataFrame(self.results).T
        df = df.sort_values('sensitivity', ascending=False)

        log.info("=" * 80)
        log.info("📊 PARAMETER SENSITIVITY RANKING")
        log.info("=" * 80)
        log.info("\n" + df.to_string())
        log.info("=" * 80)

        return df


# ============================================================================
# GENERALIZATION GAP ANALYSIS
# ============================================================================

class GeneralizationGapAnalysis:
    """Analyze generalization gap (overfitting/underfitting)."""

    def __init__(self):
        """Initialize generalization gap analysis."""
        log.info("✅ GeneralizationGapAnalysis initialized")

    def analyze_gap(self, train_scores: List[float], val_scores: List[float],
                    param_name: str = "Parameter") -> Dict[str, Any]:
        """
        Analyze generalization gap.

        Args:
            train_scores: Training scores
            val_scores: Validation scores
            param_name: Parameter being analyzed

        Returns:
            Dictionary with gap analysis results
        """
        train_scores = np.array(train_scores)
        val_scores = np.array(val_scores)

        # Gap metrics
        mean_train = np.mean(train_scores)
        mean_val = np.mean(val_scores)
        gap = mean_train - mean_val
        gap_ratio = gap / mean_train if mean_train != 0 else 0

        # Variance metrics
        train_std = np.std(train_scores)
        val_std = np.std(val_scores)

        log.info("=" * 80)
        log.info(f"📊 GENERALIZATION GAP ANALYSIS: {param_name}")
        log.info("=" * 80)
        log.info(f"  Training Mean: {mean_train:.4f}")
        log.info(f"  Validation Mean: {mean_val:.4f}")
        log.info(f"  Generalization Gap: {gap:.4f}")
        log.info(f"  Gap Ratio: {gap_ratio:.4f}")
        log.info(f"  Training Std: {train_std:.4f}")
        log.info(f"  Validation Std: {val_std:.4f}")

        # Classification
        if gap < 0.02:
            status = "✅ Well-generalized"
        elif gap < 0.05:
            status = "⚠️  Slight overfitting"
        elif gap < 0.10:
            status = "⚠️  Moderate overfitting"
        else:
            status = "❌ Severe overfitting"

        log.info(f"  Status: {status}")
        log.info("=" * 80)

        return {
            'parameter': param_name,
            'train_mean': float(mean_train),
            'val_mean': float(mean_val),
            'generalization_gap': float(gap),
            'gap_ratio': float(gap_ratio),
            'train_std': float(train_std),
            'val_std': float(val_std),
            'status': status
        }


# ============================================================================
# PARAMETER IMPORTANCE
# ============================================================================

class ParameterImportance:
    """Calculate parameter importance for hyperparameter tuning."""

    def __init__(self):
        """Initialize parameter importance."""
        self.importances = {}

        log.info("✅ ParameterImportance initialized")

    def calculate_importance(self, param_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate importance scores for parameters.

        Args:
            param_results: {param_name: sensitivity_results}

        Returns:
            Dictionary of importance scores
        """
        importances = {}

        for param_name, results in param_results.items():
            # Weight by sensitivity and score range
            sensitivity = results.get('sensitivity', 0)
            score_range = results.get('score_range', 0)

            # Combined importance metric
            importance = (sensitivity + score_range) / 2
            importances[param_name] = importance

        # Normalize
        if importances:
            total = sum(importances.values())
            importances = {k: v / total for k, v in importances.items()}

        self.importances = importances

        log.info("=" * 80)
        log.info("📊 PARAMETER IMPORTANCE RANKING")
        log.info("=" * 80)

        sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        for param, imp in sorted_imp:
            log.info(f"  {param}: {imp:.4f}")

        log.info("=" * 80)

        return importances

    def get_top_parameters(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get top N most important parameters."""
        sorted_imp = sorted(self.importances.items(), key=lambda x: x[1], reverse=True)
        return sorted_imp[:top_n]


# ============================================================================
# HYPERPARAMETER OPTIMIZATION SUGGESTIONS
# ============================================================================

class OptimizationSuggestions:
    """Generate optimization suggestions based on analysis."""

    @staticmethod
    def analyze_parameter_relationship(param_values: List[Any],
                                       scores: List[float]) -> Dict[str, Any]:
        """
        Analyze relationship between parameter and score.

        Returns:
            Dictionary with relationship analysis
        """
        scores = np.array(scores)

        try:
            param_numeric = np.array([float(p) for p in param_values])
        except:
            return {'relationship': 'unknown', 'suggestions': []}

        # Fit polynomial
        coeffs = np.polyfit(param_numeric, scores, 2)

        # Determine relationship
        if abs(coeffs[0]) > abs(coeffs[1]):
            # Quadratic
            relationship = "quadratic"
            # Find vertex
            vertex_x = -coeffs[1] / (2 * coeffs[0])
            vertex_y = np.polyval(coeffs, vertex_x)

            if coeffs[0] > 0:
                suggestion = f"U-shaped curve. Optimal around {vertex_x:.4f}"
            else:
                suggestion = f"Inverted U-shaped curve. Optimal around {vertex_x:.4f}"
        else:
            # Linear
            if coeffs[1] > 0:
                relationship = "positive_linear"
                suggestion = "Increasing with parameter. Try higher values."
            else:
                relationship = "negative_linear"
                suggestion = "Decreasing with parameter. Try lower values."

        return {
            'relationship': relationship,
            'suggestion': suggestion,
            'coefficients': coeffs.tolist()
        }

    @staticmethod
    def generate_suggestions(analysis_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Generate optimization suggestions from analysis.

        Args:
            analysis_results: Results from sensitivity analysis

        Returns:
            List of suggestions
        """
        suggestions = []

        log.info("=" * 80)
        log.info("💡 OPTIMIZATION SUGGESTIONS")
        log.info("=" * 80)

        for param_name, results in analysis_results.items():
            sensitivity = results.get('sensitivity', 0)
            gap = results.get('generalization_gap', 0)

            # High sensitivity
            if sensitivity > 0.1:
                msg = f"🔴 {param_name}: HIGH sensitivity. Tune carefully with fine granularity."
                suggestions.append(msg)
                log.info(f"  {msg}")

            # Moderate sensitivity
            elif sensitivity > 0.05:
                msg = f"🟡 {param_name}: MODERATE sensitivity. Consider for tuning."
                suggestions.append(msg)
                log.info(f"  {msg}")

            # Low sensitivity
            else:
                msg = f"🟢 {param_name}: LOW sensitivity. Use default values."
                suggestions.append(msg)
                log.info(f"  {msg}")

        log.info("=" * 80)

        return suggestions


# ============================================================================
# LEARNING DYNAMICS ANALYSIS
# ============================================================================

class LearningDynamicsAnalysis:
    """Analyze learning dynamics during training."""

    def __init__(self):
        """Initialize learning dynamics analysis."""
        log.info("✅ LearningDynamicsAnalysis initialized")

    def analyze_convergence(self, train_scores: List[float],
                            epoch_numbers: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Analyze model convergence during training.

        Args:
            train_scores: Scores across training epochs
            epoch_numbers: Epoch indices (if None, use range)

        Returns:
            Dictionary with convergence analysis
        """
        train_scores = np.array(train_scores)

        if epoch_numbers is None:
            epoch_numbers = np.arange(len(train_scores))

        # Convergence metrics
        final_score = train_scores[-1]
        max_score = np.max(train_scores)
        initial_score = train_scores[0]

        # Improvement
        total_improvement = final_score - initial_score
        improvement_ratio = total_improvement / abs(initial_score) if initial_score != 0 else 0

        # Learning rate (slope in middle section)
        mid_point = len(train_scores) // 2
        early_mean = np.mean(train_scores[:mid_point])
        late_mean = np.mean(train_scores[mid_point:])
        learning_rate = (late_mean - early_mean) / mid_point if mid_point != 0 else 0

        # Convergence status
        scores_diff = np.abs(np.diff(train_scores))
        converged = np.mean(scores_diff[-10:]) < 0.001 if len(train_scores) >= 10 else False

        log.info("=" * 80)
        log.info("📊 LEARNING DYNAMICS ANALYSIS")
        log.info("=" * 80)
        log.info(f"  Initial Score: {initial_score:.4f}")
        log.info(f"  Final Score: {final_score:.4f}")
        log.info(f"  Max Score: {max_score:.4f}")
        log.info(f"  Total Improvement: {total_improvement:.4f}")
        log.info(f"  Improvement Ratio: {improvement_ratio:.4f}")
        log.info(f"  Learning Rate: {learning_rate:.6f}")
        log.info(f"  Converged: {converged}")
        log.info("=" * 80)

        return {
            'initial_score': float(initial_score),
            'final_score': float(final_score),
            'max_score': float(max_score),
            'total_improvement': float(total_improvement),
            'improvement_ratio': float(improvement_ratio),
            'learning_rate': float(learning_rate),
            'converged': bool(converged),
            'n_epochs': len(train_scores)
        }

    def identify_overfitting_epoch(self, train_scores: List[float],
                                   val_scores: List[float]) -> Optional[int]:
        """
        Identify epoch where overfitting begins.

        Returns:
            Epoch number where overfitting starts (None if not found)
        """
        train_scores = np.array(train_scores)
        val_scores = np.array(val_scores)

        gaps = train_scores - val_scores

        # Find where gap starts increasing consistently
        for i in range(1, len(gaps)):
            # Check if gap is increasing for 3+ consecutive epochs
            if i >= 3:
                if all(gaps[j] < gaps[j+1] for j in range(i-3, i)):
                    log.info(f"⚠️  Overfitting detected starting at epoch {i}")
                    return i

        return None


# ============================================================================
# COMPREHENSIVE HYPERPARAMETER ANALYZER
# ============================================================================

class ComprehensiveHyperparameterAnalyzer:
    """Master class for comprehensive hyperparameter analysis."""

    def __init__(self):
        """Initialize comprehensive analyzer."""
        self.sensitivity = SensitivityAnalysis()
        self.gap_analysis = GeneralizationGapAnalysis()
        self.importance = ParameterImportance()
        self.learning_dynamics = LearningDynamicsAnalysis()

        self.analysis_results = {}

        log.info("✅ ComprehensiveHyperparameterAnalyzer initialized")

    def analyze_parameter_grid(self, grid_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Analyze full hyperparameter grid search results.

        Args:
            grid_results: {param_values_tuple: {'score': float, 'train_score': float}}

        Returns:
            DataFrame with analysis results
        """
        log.info("\n" + "=" * 80)
        log.info("📊 COMPREHENSIVE HYPERPARAMETER GRID ANALYSIS")
        log.info("=" * 80)

        results = []

        for params, metrics in grid_results.items():
            result = {
                'parameters': str(params),
                'score': metrics.get('score'),
                'train_score': metrics.get('train_score'),
                'gap': metrics.get('train_score', 0) - metrics.get('score', 0)
            }
            results.append(result)

        df = pd.DataFrame(results)
        df = df.sort_values('score', ascending=False)

        log.info("\n" + df.to_string())
        log.info("=" * 80)

        return df

    def generate_report(self, sensitivity_results: Dict[str, Dict[str, Any]],
                        gap_results: Dict[str, Dict[str, Any]],
                        learning_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate comprehensive hyperparameter analysis report.

        Returns:
            Formatted report string
        """
        log.info("\n" + "=" * 80)
        log.info("📊 COMPREHENSIVE HYPERPARAMETER ANALYSIS REPORT")
        log.info("=" * 80)

        lines = []

        # Sensitivity Summary
        lines.append("\n--- SENSITIVITY ANALYSIS ---")
        for param, results in sensitivity_results.items():
            lines.append(f"\n{param}:")
            lines.append(f"  Sensitivity: {results['sensitivity']:.4f}")
            lines.append(f"  Optimal Value: {results['optimal_value']}")
            lines.append(f"  Best Score: {results['optimal_score']:.4f}")

        # Gap Analysis Summary
        lines.append("\n\n--- GENERALIZATION GAP ANALYSIS ---")
        for param, results in gap_results.items():
            lines.append(f"\n{param}:")
            lines.append(f"  Gap: {results['generalization_gap']:.4f}")
            lines.append(f"  Status: {results['status']}")

        # Learning Dynamics Summary
        lines.append("\n\n--- LEARNING DYNAMICS ---")
        for param, results in learning_results.items():
            lines.append(f"\n{param}:")
            lines.append(f"  Improvement: {results['improvement_ratio']:.4f}")
            lines.append(f"  Converged: {results['converged']}")

        # Parameter Importance
        lines.append("\n\n--- PARAMETER IMPORTANCE ---")
        importance = self.importance.calculate_importance(sensitivity_results)
        for param, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {param}: {imp:.4f}")

        # Recommendations
        lines.append("\n\n--- RECOMMENDATIONS ---")
        suggestions = OptimizationSuggestions.generate_suggestions(sensitivity_results)
        for suggestion in suggestions:
            lines.append(f"  {suggestion}")

        lines.append("\n" + "=" * 80)

        report = "\n".join(lines)
        log.info(report)

        return report


if __name__ == "__main__":
    print("✅ Phase 5.6: Hyperparameter Analysis - READY")