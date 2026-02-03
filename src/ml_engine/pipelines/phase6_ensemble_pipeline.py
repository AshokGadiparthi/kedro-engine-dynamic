"""
PHASE 6: ENSEMBLE METHODS - KEDRO PIPELINE
=====================================================================
Production-ready Kedro pipeline for ensemble methods

Integrates with Phase 4 algorithms to create advanced ensembles:
  - Stacking (multi-level)
  - Blending (fast)
  - Weighted voting
  - Ensemble analysis

Author: ML Engine Team
Status: PRODUCTION READY
Integration: Kedro 0.19.5+
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
import pickle
import json
from pathlib import Path

from kedro.pipeline import Pipeline, node

log = logging.getLogger(__name__)


# ============================================================================
# KEDRO PIPELINE FUNCTIONS (Nodes)
# ============================================================================

def orchestrate_ensemble_methods(
        X_train_selected: pd.DataFrame,
        X_test_selected: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        phase4_models: Dict[str, Any],
        ensemble_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main ensemble orchestration node.
    Combines multiple ensemble methods and returns results.

    Args:
        X_train_selected: Training features from Phase 5
        X_test_selected: Test features from Phase 5
        y_train: Training labels
        y_test: Test labels
        phase4_models: Trained models from Phase 4
        ensemble_config: Configuration dict with ensemble settings

    Returns:
        Dictionary with ensemble results
    """
    from phase6_ensemble import (
        StackingEnsemble, BlendingEnsemble, WeightedVotingEnsemble,
        EnsembleAnalyzer, plot_ensemble_comparison
    )

    log.info("="*80)
    log.info("🚀 PHASE 6: ENSEMBLE METHODS ORCHESTRATION")
    log.info("="*80)

    # Prepare base models from Phase 4
    log.info("\n📦 Preparing base models from Phase 4...")
    base_models_list = []

    if 'fitted_models' in phase4_models:
        fitted_models = phase4_models['fitted_models']
        for model_name, model_obj in fitted_models.items():
            base_models_list.append((model_name, model_obj))
            log.info(f"  ✓ {model_name}")

    if not base_models_list:
        log.error("❌ No Phase 4 models available!")
        return {}

    log.info(f"\n✅ {len(base_models_list)} base models loaded")

    # Detect problem type
    is_classification = len(y_train.unique()) <= 20
    problem_type = 'classification' if is_classification else 'regression'

    log.info(f"Problem type: {problem_type}")

    ensemble_results = {}

    # ========================================================================
    # METHOD 1: STACKING
    # ========================================================================

    if ensemble_config.get('enable_stacking', True):
        log.info("\n" + "="*80)
        log.info("1️⃣  STACKING ENSEMBLE")
        log.info("="*80)

        try:
            stacking = StackingEnsemble(
                base_models=base_models_list,
                problem_type=problem_type,
                cv=5,
                random_state=42
            )

            stacking.fit(X_train_selected, y_train)
            y_pred_stack = stacking.predict(X_test_selected)

            if problem_type == 'classification':
                from sklearn.metrics import accuracy_score
                stack_score = accuracy_score(y_test, y_pred_stack)
                log.info(f"  Stacking Accuracy: {stack_score:.4f}")
            else:
                from sklearn.metrics import r2_score
                stack_score = r2_score(y_test, y_pred_stack)
                log.info(f"  Stacking R²: {stack_score:.4f}")

            ensemble_results['stacking'] = {
                'model': stacking,
                'predictions': y_pred_stack,
                'score': stack_score
            }
        except Exception as e:
            log.error(f"  ❌ Stacking failed: {str(e)[:100]}")

    # ========================================================================
    # METHOD 2: BLENDING
    # ========================================================================

    if ensemble_config.get('enable_blending', True):
        log.info("\n" + "="*80)
        log.info("2️⃣  BLENDING ENSEMBLE (FAST)")
        log.info("="*80)

        try:
            blending = BlendingEnsemble(
                base_models=base_models_list,
                holdout_fraction=0.2,
                problem_type=problem_type,
                random_state=42
            )

            blending.fit(X_train_selected, y_train)
            y_pred_blend = blending.predict(X_test_selected)

            if problem_type == 'classification':
                from sklearn.metrics import accuracy_score
                blend_score = accuracy_score(y_test, y_pred_blend)
                log.info(f"  Blending Accuracy: {blend_score:.4f}")
            else:
                from sklearn.metrics import r2_score
                blend_score = r2_score(y_test, y_pred_blend)
                log.info(f"  Blending R²: {blend_score:.4f}")

            ensemble_results['blending'] = {
                'model': blending,
                'predictions': y_pred_blend,
                'score': blend_score,
                'weights': blending.weights
            }
        except Exception as e:
            log.error(f"  ❌ Blending failed: {str(e)[:100]}")

    # ========================================================================
    # METHOD 3: WEIGHTED VOTING
    # ========================================================================

    if ensemble_config.get('enable_voting', True):
        log.info("\n" + "="*80)
        log.info("3️⃣  WEIGHTED VOTING ENSEMBLE")
        log.info("="*80)

        try:
            voting = WeightedVotingEnsemble(
                base_models=base_models_list,
                problem_type=problem_type,
                random_state=42
            )

            voting.fit(X_train_selected, y_train)
            y_pred_vote = voting.predict(X_test_selected)

            if problem_type == 'classification':
                from sklearn.metrics import accuracy_score
                vote_score = accuracy_score(y_test, y_pred_vote)
                log.info(f"  Voting Accuracy: {vote_score:.4f}")
            else:
                from sklearn.metrics import r2_score
                vote_score = r2_score(y_test, y_pred_vote)
                log.info(f"  Voting R²: {vote_score:.4f}")

            ensemble_results['voting'] = {
                'model': voting,
                'predictions': y_pred_vote,
                'score': vote_score,
                'weights': voting.weights
            }
        except Exception as e:
            log.error(f"  ❌ Voting failed: {str(e)[:100]}")

    # ========================================================================
    # ANALYSIS
    # ========================================================================

    log.info("\n" + "="*80)
    log.info("📊 ENSEMBLE ANALYSIS")
    log.info("="*80)

    # Collect predictions for analysis
    analysis_predictions = {}
    best_ensemble = None
    best_score = -1

    for method_name, result in ensemble_results.items():
        predictions = result['predictions']
        score = result['score']

        analysis_predictions[f"{method_name}_ensemble"] = predictions

        log.info(f"\n{method_name.upper()}:")
        log.info(f"  Score: {score:.4f}")

        if score > best_score:
            best_score = score
            best_ensemble = method_name

    if best_ensemble:
        log.info(f"\n🏆 Best ensemble: {best_ensemble.upper()} ({best_score:.4f})")

    # Create summary
    summary = {
        'ensemble_results': ensemble_results,
        'analysis_predictions': analysis_predictions,
        'best_ensemble': best_ensemble,
        'best_score': best_score,
        'problem_type': problem_type,
        'n_base_models': len(base_models_list),
        'base_model_names': [name for name, _ in base_models_list]
    }

    log.info("\n" + "="*80)
    log.info("✅ PHASE 6: ENSEMBLE ORCHESTRATION COMPLETE")
    log.info("="*80 + "\n")

    return summary


def save_ensemble_results(
        ensemble_summary: Dict[str, Any],
        output_path: str = 'data/06_models'
) -> Dict[str, str]:
    """
    Save ensemble results to disk.

    Args:
        ensemble_summary: Results from ensemble orchestration
        output_path: Path to save results

    Returns:
        Dictionary with file paths
    """
    from pathlib import Path

    log.info("\n" + "="*80)
    log.info("💾 SAVING ENSEMBLE RESULTS")
    log.info("="*80)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # Save each ensemble model
    for method_name, result in ensemble_summary.get('ensemble_results', {}).items():
        model_path = output_dir / f"ensemble_{method_name}.pkl"

        with open(model_path, 'wb') as f:
            pickle.dump(result['model'], f)

        saved_files[f"ensemble_{method_name}"] = str(model_path)
        log.info(f"  ✓ {model_path}")

    # Save summary JSON
    summary_path = output_dir / "ensemble_summary.json"

    summary_json = {
        'best_ensemble': ensemble_summary['best_ensemble'],
        'best_score': float(ensemble_summary['best_score']),
        'problem_type': ensemble_summary['problem_type'],
        'n_base_models': ensemble_summary['n_base_models'],
        'base_model_names': ensemble_summary['base_model_names'],
        'methods': list(ensemble_summary['ensemble_results'].keys())
    }

    with open(summary_path, 'w') as f:
        json.dump(summary_json, f, indent=2)

    saved_files['summary'] = str(summary_path)
    log.info(f"  ✓ {summary_path}")

    log.info("="*80 + "\n")

    return saved_files


# ============================================================================
# KEDRO PIPELINE DEFINITION
# ============================================================================

def create_pipeline() -> Pipeline:
    """
    Create Phase 6 Ensemble Methods Kedro pipeline.

    Returns:
        Kedro Pipeline object
    """

    log.info("\n" + "="*80)
    log.info("🔧 CREATING PHASE 6 PIPELINE")
    log.info("="*80)

    pipeline = Pipeline([
        node(
            func=orchestrate_ensemble_methods,
            inputs=[
                'X_train_selected',  # From Phase 5
                'X_test_selected',   # From Phase 5
                'y_train',           # From Phase 1
                'y_test',            # From Phase 1
                'phase4_models',     # From Phase 4
                'params:phase6'      # Configuration
            ],
            outputs='ensemble_summary',
            name='ensemble_orchestration'
        ),
        node(
            func=save_ensemble_results,
            inputs='ensemble_summary',
            outputs='ensemble_files',
            name='save_ensemble_results'
        )
    ])

    log.info("✅ Phase 6 Pipeline created successfully")
    log.info("="*80 + "\n")

    return pipeline


if __name__ == '__main__':
    log.info("Phase 6 Kedro Pipeline - Ready to use")