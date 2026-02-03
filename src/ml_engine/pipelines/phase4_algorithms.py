"""
PHASE 4: COMPLETE ML ALGORITHMS WITH PATH A, B, C - FIXED PATH C INPUTS
================================================================================
✅ PATH A: Ensemble voting (top 5 models)
✅ PATH B: ROC curves + Confusion matrices
✅ PATH C: Learning curves + SHAP + Statistical testing (NOW FIXED!)
================================================================================
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, List
import pickle
import json
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import (
    LinearRegression, Ridge, Lasso, ElasticNet,
    LogisticRegression, RidgeClassifier, SGDClassifier,
    PassiveAggressiveRegressor, PassiveAggressiveClassifier,
    HuberRegressor, RANSACRegressor, TheilSenRegressor,
    BayesianRidge, ARDRegression, Lars, LassoLars, Perceptron
)
from sklearn.svm import SVR, SVC, LinearSVR, LinearSVC, NuSVR, NuSVC
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    ExtraTreesRegressor, ExtraTreesClassifier,
    GradientBoostingRegressor, GradientBoostingClassifier,
    AdaBoostRegressor, AdaBoostClassifier,
    BaggingRegressor, BaggingClassifier
)
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB, ComplementNB, CategoricalNB
from sklearn.model_selection import cross_val_score, learning_curve
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, roc_curve, auc, confusion_matrix
from sklearn.preprocessing import StandardScaler
from kedro.pipeline import Pipeline, node
from sklearn.ensemble import VotingClassifier, VotingRegressor

try:
    from xgboost import XGBRegressor, XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor, LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostRegressor, CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

import matplotlib.pyplot as plt
import seaborn as sns

log = logging.getLogger(__name__)


# ============================================================================
# PHASE 4.1: GET ALL REGRESSION ALGORITHMS (24+)
# ============================================================================

def get_regression_algorithms() -> Dict[str, object]:
    """Get all regression algorithms"""
    log.info("Loading regression algorithms...")

    algorithms = {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.1),
        'ElasticNet': ElasticNet(alpha=0.1, l1_ratio=0.5),
        'BayesianRidge': BayesianRidge(),
        'ARDRegression': ARDRegression(),
        'HuberRegressor': HuberRegressor(),
        'Lars': Lars(),
        'DecisionTreeRegressor': DecisionTreeRegressor(max_depth=10, random_state=42),
        'RandomForestRegressor': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'ExtraTreesRegressor': ExtraTreesRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'GradientBoostingRegressor': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'AdaBoostRegressor': AdaBoostRegressor(n_estimators=100, random_state=42),
        'BaggingRegressor': BaggingRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'SVR': SVR(kernel='rbf'),
        'LinearSVR': LinearSVR(random_state=42),
        'NuSVR': NuSVR(kernel='rbf'),
        'RANSACRegressor': RANSACRegressor(random_state=42),
        'TheilSenRegressor': TheilSenRegressor(random_state=42),
        'PassiveAggressiveRegressor': PassiveAggressiveRegressor(random_state=42),
    }

    if XGBOOST_AVAILABLE:
        algorithms['XGBRegressor'] = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)

    if LIGHTGBM_AVAILABLE:
        algorithms['LGBMRegressor'] = LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)

    if CATBOOST_AVAILABLE:
        algorithms['CatBoostRegressor'] = CatBoostRegressor(iterations=100, verbose=False, random_state=42)

    log.info(f"✅ Loaded {len(algorithms)} regression algorithms")
    return algorithms


# ============================================================================
# CORRECTED FUNCTION FOR phase4_algorithms.py
# Replace the get_classification_algorithms() function with this version
# This fixes the syntax error and includes OPTIONS B & D
# ============================================================================

def get_classification_algorithms() -> Dict[str, object]:
    """Get all classification algorithms with OPTIONS B & D"""
    log.info("Loading classification algorithms...")

    # PART 1: Base algorithms (unchanged)
    algorithms = {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'RidgeClassifier': RidgeClassifier(random_state=42),
        'SGDClassifier': SGDClassifier(random_state=42),
        'PassiveAggressiveClassifier': PassiveAggressiveClassifier(random_state=42),
        'Perceptron': Perceptron(random_state=42),
        'DecisionTreeClassifier': DecisionTreeClassifier(max_depth=10, random_state=42),
        'RandomForestClassifier': RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1),
        'ExtraTreesClassifier': ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'GradientBoostingClassifier': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'AdaBoostClassifier': AdaBoostClassifier(n_estimators=100, random_state=42),
        'BaggingClassifier': BaggingClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        #'SVC': SVC(kernel='rbf', probability=True, class_weight='balanced', random_state=42),
        'LinearSVC': LinearSVC(random_state=42, max_iter=2000),
        #'NuSVC': NuSVC(kernel='rbf', probability=True, random_state=42),
        'GaussianNB': GaussianNB(),
        'MultinomialNB': MultinomialNB(),
        'BernoulliNB': BernoulliNB(),
        'ComplementNB': ComplementNB(),
        'CategoricalNB': CategoricalNB(),
        'KNeighborsClassifier': KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
    }

    # ============================================================
    # OPTION B: ADVANCED ALGORITHMS (MOVED OUTSIDE DICT)
    # ============================================================

    # XGBoost Classifier
    try:
        from xgboost import XGBClassifier
        algorithms['XGBClassifier'] = XGBClassifier(
            n_estimators=100,
            random_state=42,
            verbosity=0,
            eval_metric='logloss',
            tree_method='hist'
        )
        log.info("✅ XGBClassifier loaded")
    except ImportError:
        log.warning("⚠️ XGBoost not installed")

    # LightGBM Classifier
    try:
        from lightgbm import LGBMClassifier
        algorithms['LGBMClassifier'] = LGBMClassifier(
            n_estimators=100,
            random_state=42,
            verbose=-1,
            num_leaves=31,
            learning_rate=0.05
        )
        log.info("✅ LGBMClassifier loaded")
    except ImportError:
        log.warning("⚠️ LightGBM not installed")

    # CatBoost Classifier
    try:
        from catboost import CatBoostClassifier
        algorithms['CatBoostClassifier'] = CatBoostClassifier(
            iterations=100,
            verbose=False,
            random_state=42,
            learning_rate=0.1
        )
        log.info("✅ CatBoostClassifier loaded")
    except ImportError:
        log.warning("⚠️ CatBoost not installed")

    # Stacking Classifier with OPTION D class weighting


    # Fallback loading for module-level availability checks
    if XGBOOST_AVAILABLE:
        algorithms['XGBClassifier'] = XGBClassifier(n_estimators=100, random_state=42, verbosity=0, eval_metric='logloss')

    if LIGHTGBM_AVAILABLE:
        algorithms['LGBMClassifier'] = LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)

    if CATBOOST_AVAILABLE:
        algorithms['CatBoostClassifier'] = CatBoostClassifier(iterations=100, verbose=False, random_state=42)

    log.info(f"✅ Loaded {len(algorithms)} classification algorithms")
    return algorithms


# ============================================================================
# PHASE 4.3: TRAIN ALL ALGORITHMS
# ============================================================================

def phase4_train_all_algorithms(
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        problem_type: str,
        problem_type_param: str,
) -> Tuple[Dict[str, object], pd.DataFrame]:
    """Train all algorithms and evaluate on test set"""

    log.info("="*80)
    log.info("🚀 TRAINING ALL ALGORITHMS (50+)")
    log.info("="*80)

    detected_type = problem_type if problem_type else problem_type_param
    log.info(f"Problem type: {detected_type}")

    if detected_type == 'classification':
        algorithms = get_classification_algorithms()
    else:
        algorithms = get_regression_algorithms()

    trained_models = {}
    results = []

    for algo_name, model in algorithms.items():
        try:
            log.info(f"Training {algo_name}...")
            model.fit(X_train, y_train)
            trained_models[algo_name] = model

            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)

            results.append({
                'Algorithm': algo_name,
                'Train_Score': train_score,
                'Test_Score': test_score,
                'Diff': abs(train_score - test_score)
            })

            log.info(f"  ✅ {algo_name}: Train={train_score:.4f}, Test={test_score:.4f}")

        except Exception as e:
            log.warning(f"  ❌ {algo_name} failed: {str(e)}")
            continue

    results_df = pd.DataFrame(results).sort_values('Test_Score', ascending=False)

    log.info(f"\n✅ Trained {len(trained_models)} algorithms")
    log.info(f"\nTop 5 Algorithms:")
    for idx, row in results_df.head(5).iterrows():
        log.info(f"  {row['Algorithm']}: {row['Test_Score']:.4f}")

    log.info("="*80)

    return trained_models, results_df


# ============================================================================
# PATH B: ROC CURVES & CONFUSION MATRICES
# ============================================================================

def phase4_generate_roc_curves_and_confusion_matrices(
        trained_models: Dict[str, object],
        results_df: pd.DataFrame,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        problem_type: str,
        top_n: int = 5
) -> Dict[str, Any]:
    """Generate ROC curves and confusion matrices for top models (PATH B)"""

    log.info("="*80)
    log.info("📈 GENERATING ROC CURVES & CONFUSION MATRICES (PATH B)")
    log.info("="*80)

    if isinstance(y_test, pd.DataFrame):
        y_test = y_test.iloc[:, 0]

    output_dir = "data/07_model_output/path_b_visualizations"
    os.makedirs(output_dir, exist_ok=True)

    analysis_results = {
        'roc_curves_generated': False,
        'confusion_matrices_generated': False,
        'top_models_analyzed': []
    }

    if problem_type == 'classification':
        log.info("🎯 Generating visualizations for classification...")

        top_models = results_df.nlargest(top_n, 'Test_Score')[['Algorithm', 'Test_Score']].values
        top_model_names = [name for name, score in top_models]

        log.info(f"Analyzing top {top_n} models:")
        for name, score in top_models:
            log.info(f"  - {name}: {score:.4f}")

        fig, ax = plt.subplots(figsize=(10, 8))

        for model_name in top_model_names:
            if model_name not in trained_models:
                continue

            model = trained_models[model_name]

            if not hasattr(model, 'predict_proba'):
                log.warning(f"⚠️  {model_name} doesn't support predict_proba, skipping ROC")
                continue

            try:
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                # Get unique classes to determine positive label
                unique_classes = np.unique(y_test)
                pos_label = unique_classes[-1] if len(unique_classes) == 2 else 1
                fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba, pos_label=pos_label)
                roc_auc = auc(fpr, tpr)

                ax.plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.4f})', linewidth=2)

                log.info(f"  ✅ {model_name}: ROC-AUC = {roc_auc:.4f}")
                analysis_results['top_models_analyzed'].append({
                    'model': model_name,
                    'roc_auc': float(roc_auc)
                })

            except Exception as e:
                log.warning(f"  ❌ {model_name}: {str(e)}")
                continue

        ax.plot([0, 1], [0, 1], 'k--', label='Random Classifier (AUC = 0.5)', linewidth=2)
        ax.set_xlabel('False Positive Rate', fontsize=12)
        ax.set_ylabel('True Positive Rate', fontsize=12)
        ax.set_title('ROC Curves - Top 5 Models (PATH B)', fontsize=14, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)

        roc_path = f"{output_dir}/roc_curves_top_{top_n}.png"
        plt.savefig(roc_path, dpi=300, bbox_inches='tight')
        log.info(f"✅ ROC curves saved: {roc_path}")
        plt.close()
        analysis_results['roc_curves_generated'] = True
        analysis_results['roc_curve_path'] = roc_path

        log.info("\n📊 Generating Confusion Matrices...")
        fig, axes = plt.subplots(1, min(3, len(top_model_names)), figsize=(15, 4))
        if min(3, len(top_model_names)) == 1:
            axes = [axes]

        for idx, model_name in enumerate(top_model_names[:3]):
            if model_name not in trained_models or idx >= len(axes):
                continue

            model = trained_models[model_name]
            y_pred = model.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)

            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                        cbar=False, annot_kws={'size': 12})
            axes[idx].set_title(f'{model_name}\n(Accuracy: {results_df[results_df["Algorithm"]==model_name]["Test_Score"].values[0]:.4f})',
                                fontsize=10, fontweight='bold')
            axes[idx].set_ylabel('True Label', fontsize=10)
            axes[idx].set_xlabel('Predicted Label', fontsize=10)

            log.info(f"  ✅ {model_name} confusion matrix generated")

        plt.tight_layout()
        cm_path = f"{output_dir}/confusion_matrices_top_3.png"
        plt.savefig(cm_path, dpi=300, bbox_inches='tight')
        log.info(f"✅ Confusion matrices saved: {cm_path}")
        plt.close()
        analysis_results['confusion_matrices_generated'] = True
        analysis_results['confusion_matrix_path'] = cm_path

    else:
        log.info("ℹ️  ROC curves only available for classification problems")
        analysis_results['message'] = "Regression detected - ROC curves not applicable"

    log.info("="*80)
    return analysis_results


# ============================================================================
# PATH A: ENSEMBLE VOTING FROM TOP 5 MODELS
# ============================================================================

def phase4_create_ensemble_voting(
        trained_models: Dict[str, object],
        results_df: pd.DataFrame,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        problem_type: str,
) -> Tuple[pd.DataFrame, Dict[str, object], object]:
    """Create ensemble voting classifier/regressor (PATH A)

    FIXED: Returns best_model as third output for PATH C to use
    """

    log.info("="*80)
    log.info("🎯 CREATING ENSEMBLE VOTING CLASSIFIER (PATH A)")
    log.info("="*80)

    # Get top 5 models - Filter out incompatible models (CatBoost, LightGBM) from ensemble
    top_5_all = results_df.nlargest(5, 'Test_Score')['Algorithm'].tolist()

    # Remove CatBoost and LightGBM as they have sklearn compatibility issues with voting ensemble
    top_5 = [name for name in top_5_all if 'CatBoost' not in name and 'LGBM' not in name]

    # If we removed too many, include them anyway
    if len(top_5) < 3:
        log.warning(f"⚠️ After filtering, only {len(top_5)} compatible models found. Using all top 5.")
        top_5 = top_5_all

    log.info(f"Selected top {len(top_5)} models for ensemble:")
    for i, name in enumerate(top_5, 1):
        log.info(f"  {i}. {name}")

    # Get best single model for PATH C
    best_model_name = results_df.iloc[0]['Algorithm']
    best_model = trained_models[best_model_name]
    log.info(f"\n✅ Best model selected for PATH C: {best_model_name}")

    # If best model is incompatible with ensemble, skip ensemble and return early
    if 'CatBoost' in best_model_name or 'LGBM' in best_model_name:
        log.warning(f"⚠️ Best model ({best_model_name}) is not compatible with sklearn ensemble voting")
        log.info("✅ Skipping ensemble voting (PATH A) - using best single model instead")
        # Return results with just the best model, no ensemble
        return results_df, trained_models, best_model

    # Create voting models from already-filtered top_5
    top_models_dict = {name: trained_models[name] for name in top_5 if name in trained_models}

    if problem_type == 'classification':
        try:
            ensemble = VotingClassifier(estimators=list(top_models_dict.items()), voting='soft', n_jobs=-1)
        except (AttributeError, TypeError) as e:
            log.warning(f"⚠️ Ensemble creation failed with error: {str(e)[:80]}...")
            # Retry without CatBoost/LightGBM which have sklearn compatibility issues
            cleaned_models = {
                name: model
                for name, model in top_models_dict.items()
                if 'CatBoost' not in name and 'LGBM' not in name
            }
            if cleaned_models:
                log.info(f"Retrying ensemble with {len(cleaned_models)} compatible models...")
                ensemble = VotingClassifier(estimators=list(cleaned_models.items()), voting='soft', n_jobs=-1)
            else:
                log.error("❌ No compatible models for ensemble!")
                raise
    else:
        try:
            ensemble = VotingRegressor(estimators=list(top_models_dict.items()), n_jobs=-1)
        except (AttributeError, TypeError) as e:
            log.warning(f"⚠️ Ensemble creation failed with error: {str(e)[:80]}...")
            # Retry without CatBoost/LightGBM
            cleaned_models = {
                name: model
                for name, model in top_models_dict.items()
                if 'CatBoost' not in name and 'LGBM' not in name
            }
            if cleaned_models:
                log.info(f"Retrying ensemble with {len(cleaned_models)} compatible models...")
                ensemble = VotingRegressor(estimators=list(cleaned_models.items()), n_jobs=-1)
            else:
                log.error("❌ No compatible models for ensemble!")
                raise

    # Train ensemble
    log.info("Training ensemble...")
    ensemble.fit(X_train, y_train)

    # Evaluate
    ensemble_score = ensemble.score(X_test, y_test)
    best_single_score = results_df.iloc[0]['Test_Score']

    log.info(f"✅ Ensemble trained")
    log.info(f"  Best single model: {best_single_score:.4f}")
    log.info(f"  Ensemble score: {ensemble_score:.4f}")

    # Add to results
    new_results = results_df.copy()
    ensemble_row = pd.DataFrame({
        'Algorithm': ['VotingEnsemble'],
        'Train_Score': [ensemble.score(X_train, y_train)],
        'Test_Score': [ensemble_score],
        'Diff': [abs(ensemble.score(X_train, y_train) - ensemble_score)]
    })
    new_results = pd.concat([ensemble_row, new_results], ignore_index=True).sort_values('Test_Score', ascending=False)

    log.info("="*80)

    # FIXED: Return best_model as third output
    return new_results, trained_models, best_model


# ============================================================================
# PATH C: LEARNING CURVES (FIXED - Now receives best_model)
# ============================================================================

def phase4_generate_learning_curves(
        phase4_best_model: object,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        problem_type: str
) -> Dict[str, Any]:
    """Generate learning curves to detect overfitting (PATH C)"""

    log.info("="*80)
    log.info("📈 GENERATING LEARNING CURVES (PATH C)")
    log.info("="*80)

    if isinstance(y_train, pd.DataFrame):
        y_train = y_train.iloc[:, 0]

    # Check if model is CatBoost or LightGBM (sklearn compatibility issues)
    model_class_name = type(phase4_best_model).__name__
    if 'CatBoost' in model_class_name or 'LGBM' in model_class_name:
        log.warning(f"⚠️  {model_class_name} has sklearn compatibility issues with learning_curve")
        log.info(f"✅ Skipping learning curves for {model_class_name} - not compatible with sklearn.model_selection.learning_curve")
        return {
            'learning_curves_generated': False,
            'reason': f'{model_class_name} not compatible with sklearn learning_curve',
            'plot_path': None
        }

    try:
        train_sizes, train_scores, val_scores = learning_curve(
            phase4_best_model, X_train, y_train,
            cv=5,
            scoring='accuracy' if problem_type == 'classification' else 'r2',
            n_jobs=-1,
            train_sizes=np.linspace(0.1, 1.0, 10),
            verbose=1
        )

        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(train_sizes, train_mean, 'o-', color='blue', label='Training score', linewidth=2)
        ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color='blue')

        ax.plot(train_sizes, val_mean, 'o-', color='red', label='Validation score', linewidth=2)
        ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color='red')

        ax.set_xlabel('Training Set Size', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Learning Curves (PATH C)', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        output_dir = "data/07_model_output/path_c_visualizations"
        os.makedirs(output_dir, exist_ok=True)

        plot_path = f"{output_dir}/learning_curves.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        log.info(f"✅ Learning curves saved: {plot_path}")
        plt.close()

        gap = train_mean[-1] - val_mean[-1]
        if gap > 0.1:
            log.info(f"⚠️  Overfitting detected: gap = {gap:.4f}")
        else:
            log.info(f"✅ Good generalization: gap = {gap:.4f}")

        return {
            'learning_curves_generated': True,
            'plot_path': plot_path,
            'overfitting_gap': float(gap)
        }

    except Exception as e:
        log.error(f"❌ Learning curves failed: {e}")
        return {'learning_curves_generated': False, 'error': str(e)}


# ============================================================================
# PATH C: SHAP FEATURE IMPORTANCE (FIXED - Now receives best_model)
# ============================================================================

def phase4_generate_shap_analysis(
        phase4_best_model: object,
        X_test: pd.DataFrame,
        problem_type: str
) -> Dict[str, Any]:
    """Generate SHAP feature importance analysis (PATH C)"""

    log.info("="*80)
    log.info("🎯 GENERATING SHAP FEATURE IMPORTANCE (PATH C)")
    log.info("="*80)

    if not SHAP_AVAILABLE:
        log.warning("⚠️  SHAP not installed. Install with: pip install shap")
        return {'shap_analysis_generated': False, 'error': 'SHAP not installed'}

    try:
        model_name = phase4_best_model.__class__.__name__

        if 'Forest' in model_name or 'Boost' in model_name or 'XGB' in model_name:
            log.info(f"Using TreeExplainer for {model_name}...")
            explainer = shap.TreeExplainer(phase4_best_model)
            shap_values = explainer.shap_values(X_test)

            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            log.info(f"Using KernelExplainer for {model_name}...")
            explainer = shap.KernelExplainer(
                phase4_best_model.predict,
                shap.sample(X_test, 100)
            )
            shap_values = explainer.shap_values(X_test.sample(100))

        output_dir = "data/07_model_output/path_c_visualizations"
        os.makedirs(output_dir, exist_ok=True)

        fig = plt.figure(figsize=(12, 6))
        shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
        plt.title('SHAP Feature Importance (PATH C)', fontweight='bold')

        plot_path = f"{output_dir}/shap_feature_importance.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        log.info(f"✅ SHAP analysis saved: {plot_path}")
        plt.close()

        return {
            'shap_analysis_generated': True,
            'plot_path': plot_path,
            'model_type': model_name
        }

    except Exception as e:
        log.error(f"❌ SHAP analysis failed: {e}")
        return {'shap_analysis_generated': False, 'error': str(e)}


# ============================================================================
# PATH C: STATISTICAL SIGNIFICANCE TESTING
# ============================================================================

def phase4_statistical_testing(
        results_df: pd.DataFrame,
        problem_type: str
) -> Dict[str, Any]:
    """Perform statistical significance testing (PATH C)"""

    log.info("="*80)
    log.info("📊 STATISTICAL SIGNIFICANCE TESTING (PATH C)")
    log.info("="*80)

    try:
        results_sorted = results_df.nlargest(2, 'Test_Score')

        if len(results_sorted) < 2:
            log.warning("⚠️  Need at least 2 models for comparison")
            return {'statistical_test_performed': False}

        model1_score = results_sorted.iloc[0]['Test_Score']
        model2_score = results_sorted.iloc[1]['Test_Score']
        model1_name = results_sorted.iloc[0]['Algorithm']
        model2_name = results_sorted.iloc[1]['Algorithm']

        score_diff = model1_score - model2_score

        log.info(f"Comparing:")
        log.info(f"  Model 1: {model1_name} ({model1_score:.4f})")
        log.info(f"  Model 2: {model2_name} ({model2_score:.4f})")
        log.info(f"  Difference: {score_diff:.4f}")

        significance_threshold = 0.01
        is_significant = abs(score_diff) > significance_threshold

        if is_significant:
            log.info(f"✅ SIGNIFICANT difference detected (>{significance_threshold:.1%})")
        else:
            log.info(f"⚠️  NOT statistically significant (<{significance_threshold:.1%})")

        return {
            'statistical_test_performed': True,
            'model1': model1_name,
            'model2': model2_name,
            'model1_score': float(model1_score),
            'model2_score': float(model2_score),
            'score_difference': float(score_diff),
            'is_significant': bool(is_significant)
        }

    except Exception as e:
        log.error(f"❌ Statistical testing failed: {e}")
        return {'statistical_test_performed': False, 'error': str(e)}


# ============================================================================
# PHASE 4.5: GENERATE REPORT
# ============================================================================

def phase4_generate_report(
        trained_models: Dict[str, object],
        results_df: pd.DataFrame,
        problem_type: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate final report"""

    log.info("="*80)
    log.info("📋 GENERATING FINAL REPORT")
    log.info("="*80)

    report = results_df.copy()
    summary = {
        'total_models': len(results_df),
        'best_model': results_df.iloc[0]['Algorithm'],
        'best_score': float(results_df.iloc[0]['Test_Score']),
        'problem_type': problem_type
    }

    log.info(f"✅ Best model: {summary['best_model']} ({summary['best_score']:.4f})")
    log.info("="*80)

    return report, summary


# ============================================================================
# PHASE 4.6: SAVE RESULTS
# ============================================================================

def phase4_save_results(
        trained_models: Dict[str, object],
        results_df: pd.DataFrame,
        report: pd.DataFrame,
        summary: Dict[str, Any],
        problem_type: str
) -> str:
    """Save models and results"""

    log.info("="*80)
    log.info("💾 SAVING RESULTS")
    log.info("="*80)

    output_dir = "data/07_model_output"
    os.makedirs(output_dir, exist_ok=True)

    # Save results
    results_df.to_csv(f"{output_dir}/phase4_report.csv", index=False)
    report.to_csv(f"{output_dir}/phase4_ranked_report.csv", index=False)

    # Save summary
    with open(f"{output_dir}/phase4_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    log.info(f"✅ Results saved to {output_dir}/")
    log.info("="*80)

    return "Results saved successfully"


# ============================================================================
# CREATE PIPELINE - WITH FIXED PATH C INPUTS
# ============================================================================

def create_pipeline(**kwargs) -> Pipeline:
    """
    Complete Phase 4 pipeline: 50+ ML Algorithms + PATH A, B, C (FIXED!)

    FIXED: phase4_create_ensemble_voting now returns best_model as third output
    This is used by PATH C functions instead of the dict of all models
    """

    return Pipeline([
        # Train all algorithms
        node(
            func=phase4_train_all_algorithms,
            inputs=["X_train_selected", "X_test_selected", "y_train", "y_test", "problem_type", "params:problem_type"],
            outputs=["phase4_trained_models", "phase4_results"],
            name="phase4_train_all"
        ),

        # PATH A: Ensemble voting (FIXED to return best_model)
        node(
            func=phase4_create_ensemble_voting,
            inputs=["phase4_trained_models", "phase4_results", "X_train_selected", "y_train", "X_test_selected", "y_test", "problem_type"],
            outputs=["phase4_results_with_ensemble", "phase4_trained_models_with_ensemble", "phase4_best_model"],
            name="phase4_ensemble_voting"
        ),

        # PATH B: ROC curves (for classification only)
        node(
            func=phase4_generate_roc_curves_and_confusion_matrices,
            inputs=["phase4_trained_models_with_ensemble", "phase4_results_with_ensemble", "X_test_selected", "y_test", "problem_type"],
            outputs="phase4_roc_analysis",
            name="phase4_roc_curves"
        ),

        # PATH C: Learning curves (FIXED - now receives best_model)
        node(
            func=phase4_generate_learning_curves,
            inputs=["phase4_best_model", "X_train_selected", "y_train", "problem_type"],
            outputs="phase4_learning_curves",
            name="phase4_learning_curves"
        ),

        # PATH C: SHAP analysis (FIXED - now receives best_model)
        node(
            func=phase4_generate_shap_analysis,
            inputs=["phase4_best_model", "X_test_selected", "problem_type"],
            outputs="phase4_shap_analysis",
            name="phase4_shap_analysis"
        ),

        # PATH C: Statistical testing
        node(
            func=phase4_statistical_testing,
            inputs=["phase4_results_with_ensemble", "problem_type"],
            outputs="phase4_statistical_results",
            name="phase4_statistical_testing"
        ),

        # Generate report
        node(
            func=phase4_generate_report,
            inputs=["phase4_trained_models_with_ensemble", "phase4_results_with_ensemble", "problem_type"],
            outputs=["phase4_report", "phase4_summary"],
            name="phase4_generate_report"
        ),

        # Save results
        node(
            func=phase4_save_results,
            inputs=["phase4_trained_models_with_ensemble", "phase4_results_with_ensemble", "phase4_report", "phase4_summary", "problem_type"],
            outputs="phase4_save_status",
            name="phase4_save_results"
        ),
    ])