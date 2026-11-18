"""Synthetic coronagraph throughput and noise-correlation diagnostics."""
import numpy as np

def matched_amplitude(image, template, covariance):
    """GLS amplitude and formal 1-sigma uncertainty for a fixed template."""
    y, t, c = np.asarray(image,float).ravel(), np.asarray(template,float).ravel(), np.asarray(covariance,float)
    if y.shape != t.shape or not y.size or c.shape != (y.size,y.size) or not all(np.all(np.isfinite(a)) for a in (y,t,c)):
        raise ValueError('invalid inputs')
    l = np.linalg.cholesky(c)
    a, b = np.linalg.solve(l,t), np.linalg.solve(l,y)
    norm = a@a
    if norm <= 0: raise ValueError('zero template')
    return float(a@b/norm), float(1/np.sqrt(norm))

def injection_recovery(background, template, amplitudes, subtractor, covariance):
    """Inject BEFORE subtraction; report recovered minus baseline and throughput.

    subtractor must be a deterministic callable mapping input image to residual image.
    """
    bg, t = np.asarray(background,float), np.asarray(template,float)
    if bg.shape != t.shape or not np.all(np.isfinite(bg)) or not np.all(np.isfinite(t)):
        raise ValueError('invalid arrays')
    baseline = np.asarray(subtractor(bg),float)
    if baseline.shape != bg.shape: raise ValueError('subtractor shape')
    base_amp, _ = matched_amplitude(baseline,t,covariance)
    result=[]
    for amplitude in amplitudes:
        if not np.isfinite(amplitude) or amplitude == 0: raise ValueError('amplitudes must be nonzero finite')
        residual = np.asarray(subtractor(bg+amplitude*t),float)
        if residual.shape != bg.shape: raise ValueError('subtractor shape')
        measured, err = matched_amplitude(residual,t,covariance)
        result.append((float(amplitude),float(measured-base_amp),float((measured-base_amp)/amplitude),err))
    return result

def equicorrelated_covariance(sigma, rho, count):
    """Equal variance and pairwise correlation, with SPD bounds."""
    if not np.isfinite(sigma) or sigma<=0 or not isinstance(count,int) or count<2 or not np.isfinite(rho) or not (-1/(count-1)<rho<1):
        raise ValueError('invalid covariance parameters')
    return sigma**2*((1-rho)*np.eye(count)+rho*np.ones((count,count)))
