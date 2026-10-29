"""Numerical V5 fitting primitives for externally approved, labelled features.

No dataset is bundled. All feature matrices, labels and animal identifiers must
be provided by the researcher. Standardization is fitted on training rows only.
"""
from __future__ import annotations
import numpy as np


def fit_ranker(features, ilm_targets, rpe_targets, *, feature_count=202,
               rpe_weight=0., ridge=.1, hard=False):
    stats=[]
    for feature,ilm,rpe in zip(features,ilm_targets,rpe_targets,strict=True):
        x=feature.matrix[:,:feature_count]
        distance=(feature.pairs[:,0]-ilm)**2+rpe_weight*(feature.pairs[:,1]-rpe)**2
        if hard:
            y=np.zeros(len(distance));y[np.argmin(distance)]=1.
        else:
            y=np.exp(-distance/(2*40.**2))
        positive=y>=max(.20,y.max()*.50)
        w=np.where(positive,.5/max(1,positive.sum()),.5/max(1,(~positive).sum()))
        stats.append((w.sum(),w@x,x.T@(w[:,None]*x),float(w@y),x.T@(w*y)))
    sw,sx,sxx,sy,sxy=[sum(s[j] for s in stats) for j in range(5)]
    mean=sx/sw
    scale=np.sqrt(np.maximum(np.diag(sxx)/sw-mean**2,1e-12))
    scale[scale<1e-6]=1.
    gram=(sxx-np.outer(sx,mean)-np.outer(mean,sx)+sw*np.outer(mean,mean))/np.outer(scale,scale)
    cross=(sx-sw*mean)/scale
    gram=np.block([[np.array([[sw]]),cross[None,:]],[cross[:,None],gram]])
    rhs=np.r_[sy,(sxy-mean*sy)/scale]
    penalty=np.eye(len(rhs))*ridge;penalty[0,0]=0.
    coefficient=np.linalg.solve(gram+penalty,rhs)
    return {"feature_count":feature_count,"feature_mean":mean.tolist(),
            "feature_scale":scale.tolist(),"coefficient":coefficient.tolist()}


def leave_one_animal_out(features, ilm_targets, rpe_targets, animal_ids, **settings):
    """Yield predictions excluding all eyes/timepoints of each held-out animal.

    Callers must also fit distance calibration and any hyperparameter search
    inside training folds. These are peak positions, not calibrated AL values.
    """
    from ls900_biometry.v5 import score_features
    animal_ids=np.asarray(animal_ids)
    ilm_targets=np.asarray(ilm_targets);rpe_targets=np.asarray(rpe_targets)
    for animal in np.unique(animal_ids):
        train=np.flatnonzero(animal_ids!=animal)
        test=np.flatnonzero(animal_ids==animal)
        model=fit_ranker([features[i] for i in train],ilm_targets[train],rpe_targets[train],**settings)
        for index in test:
            yield int(index),score_features(features[index],model)
