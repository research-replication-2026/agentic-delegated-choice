"""Scenario-level inference; conservative corroboration of bootstrap-t and t49.

Primary p=max(p_bootstrap_t, p_t49), followed by Holm across four contrasts.
Sensitivity uses bootstrap-t alone. No finite-sample exactness is asserted.
"""
import numpy as np
from scipy.stats import t


def studentize(numerator, se):
    numerator=np.asarray(numerator,dtype=float);se=np.asarray(se,dtype=float)
    fallback=np.where(np.abs(numerator)<1e-13,0.,np.where(numerator>0,np.inf,-np.inf))
    return np.divide(numerator,se,out=np.array(fallback,copy=True),where=se>1e-13)


def tail_p(reference, observed):
    """Equal-tailed two-sided Monte Carlo p; do not force a symmetric |t| law."""
    b=len(reference)
    return float(min(1.,2*min((1+np.sum(reference<=observed))/(b+1),(1+np.sum(reference>=observed))/(b+1))))


def mammen_weights(rng, shape):
    root=np.sqrt(5);negative=(1-root)/2;positive=(1+root)/2
    prob_negative=(root+1)/(2*root)
    return np.where(rng.random(shape)<prob_negative,negative,positive)


def infer(values, seed=2026102102, draws=49999, sensitivity_draws=49999):
    d=np.asarray(values,dtype=float)
    if d.ndim!=1 or len(d)!=50 or not np.isfinite(d).all():
        raise ValueError('Require 50 finite scenario-level paired means')
    n=len(d);estimate=float(d.mean());se=float(d.std(ddof=1)/np.sqrt(n))
    if se<1e-13:
        return dict(estimate=estimate,se=se,status='degenerate_cluster_variance_no_bootstrap_inference',p_primary=1.,p_sensitivity=1.,ci95=[-1.,1.],ci9875=[-1.,1.],degenerate_bootstrap_draws=draws)
    observed=float(estimate/se)
    rng=np.random.default_rng(seed)
    samples=d[rng.integers(0,n,(draws,n))]
    bse=samples.std(axis=1,ddof=1)/np.sqrt(n)
    reference=studentize(samples.mean(axis=1)-estimate,bse)
    def interval(alpha):
        # Order-statistic quantiles avoid interpolating +inf/-inf in sparse samples.
        q=np.quantile(reference,[alpha/2,1-alpha/2],method='inverted_cdf')
        return np.clip([estimate-se*q[1],estimate-se*q[0]],-1,1).tolist()
    pair_p=tail_p(reference,observed);t_p=float(2*t.sf(abs(observed),49))
    boot95=interval(.05);boot9875=interval(.0125)
    def envelope(ci,alpha):
        hw=float(t.ppf(1-alpha/2,49)*se)
        return [float(max(-1,min(ci[0],estimate-hw))),float(min(1,max(ci[1],estimate+hw)))]
    return dict(estimate=estimate,se=se,status='bootstrap_t_with_conservative_t49_corroboration',p_primary=max(pair_p,t_p),p_sensitivity=pair_p,ci95=envelope(boot95,.05),ci9875=envelope(boot9875,.0125),bootstrap_t_ci95=boot95,bootstrap_t_ci9875=boot9875,t49_diagnostic_p=t_p,degenerate_bootstrap_draws=int(np.sum(bse<1e-13)),draws=draws,seed=seed,primary='max(equal-tailed scenario pairs bootstrap-t p, t49 p); CI envelope',sensitivity='equal-tailed scenario pairs bootstrap-t alone')
