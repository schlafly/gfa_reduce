from .kentools_center import kentools_center
import numpy as np
import astropy.io.fits as fits
# run astrometric calibration given a catalog with the centroids and
# an initial guess (SKYRA, SKYDEC) of the field of view center
# mainly going to be a wrapper for kentools_center

def recalib_astrom(cat, fname_raw):
    # cat should be the catalog for an entire exposure

    extnames = np.unique(cat['camera'])

    h = fits.getheader(fname_raw, extname='GFA')

    result = []
    for extname in extnames:
        result.append(kentools_center(cat[cat['camera'] == extname],
                                      h['SKYRA'], h['SKYDEC'],
                                      extname=extname))

    return result
