import numpy as np
import xgboost as xgb

# 1. load model
bst = xgb.Booster()
bst.load_model("xgb_model.json")

# 2. load feature order (from R)
with open("feature_order.txt", "r", encoding="utf-8") as f:
    FEATURE_ORDER = [line.strip() for line in f if line.strip()]

def yn_to_int(v: str) -> int:
    return 0 if v == "No" else 1

def predict_flu_probability(
    temp, height, weight, DOI, WOS, season,
    rr, sbp, o2s, pulse,
    fluvaccine, cough, coughsputum, sorethroat,
    rhinorrhea, sinuspain, exposehuman, travel,
    medhistav, pastmedchronlundis
) -> float:
    """
    完全等價於 R 的 pred_tit()
    回傳：Positive class probability (%)
    """

    inputs = {
        "temp": float(temp),
        "height": float(height),
        "weight": float(weight),
        "DOI": float(DOI),
        "WOS": float(WOS),
        "season": float(season),
        "rr": float(rr),
        "sbp": float(sbp),
        "o2s": float(o2s),
        "pulse": float(pulse),
        "fluvaccine": yn_to_int(fluvaccine),
        "cough": yn_to_int(cough),
        "coughsputum": yn_to_int(coughsputum),
        "sorethroat": yn_to_int(sorethroat),
        "rhinorrhea": yn_to_int(rhinorrhea),
        "sinuspain": yn_to_int(sinuspain),
        "exposehuman": yn_to_int(exposehuman),
        "travel": yn_to_int(travel),
        "medhistav": yn_to_int(medhistav),
        "pastmedchronlundis": yn_to_int(pastmedchronlundis),
    }

    X = np.array([[inputs[f] for f in FEATURE_ORDER]], dtype=np.float32)
    dmat = xgb.DMatrix(X)

    # model outputs Negative class prob
    prob_negative = bst.predict(dmat)[0]
    prob_positive = 1.0 - prob_negative

    return prob_positive * 100.0
