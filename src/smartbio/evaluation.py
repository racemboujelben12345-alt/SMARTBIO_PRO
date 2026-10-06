import numpy as np

def regression_metrics(y_true, y_pred):
    y,p = np.asarray(y_true,float), np.asarray(y_pred,float)
    e = p-y
    ss_res, ss_tot = np.sum(e**2), np.sum((y-y.mean())**2)
    return {
        "n": int(len(y)),
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e**2))),
        "r2": float(1-ss_res/ss_tot) if ss_tot else float("nan"),
        "pearson_r": float(np.corrcoef(y,p)[0,1]) if len(y)>1 else float("nan"),
        "bias": float(np.mean(e)),
    }

def bland_altman(y_true, y_pred):
    y,p = np.asarray(y_true,float), np.asarray(y_pred,float)
    d = p-y
    bias = d.mean()
    sd = d.std(ddof=1)
    return {
        "bias":float(bias),
        "loa_lower":float(bias-1.96*sd),
        "loa_upper":float(bias+1.96*sd),
    }

def coverage_under_uncertainty(y_true, pred, uncertainty, z=1.96):
    y,p,u = map(lambda x: np.asarray(x,float), (y_true,pred,uncertainty))
    inside = np.abs(y-p) <= z*u
    return {"coverage":float(np.mean(inside)), "n":int(len(y))}
