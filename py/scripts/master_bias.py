import ci_reduce.common as common
import astropy.io.fits as fits
import glob
import numpy as np
import os

# currently I have access to 4 independent bias exposures for each of
# CIE, CIN, CIS, and CIW, and none for CIC
# these available data come from "forDK.tar.gz" samples, where
# CIC was in "simulation mode"

engdir = '/project/projectdirs/desi/users/ameisner/CI/FORDK'

def get_bias_frame_names():
    flist = glob.glob(engdir + '/*/*.fits.fz')
    flist = np.array(flist)
    nobin_pos = np.array([f.find('NOBIN') for f in flist])
    flist = flist[nobin_pos != -1]

    acttime = np.zeros(len(flist))
    for i, f in enumerate(flist):
        h = fits.getheader(f)
        acttime[i] = h['ACTTIME']

    flist = flist[acttime == 0]
    return flist

def read_bias_frames(ci_extname):
    flist = get_bias_frame_names()
    imgs = [fits.getdata(f, extname=ci_extname) for f in flist]

    return imgs

def master_bias_1camera(ci_extname):
    # use common to check that CI extention name is valid

    assert(ci_extname != 'CIC')

    if ci_extname != 'CIC':
        bias_frames = read_bias_frames(ci_extname)
        bias_frames = np.asarray(bias_frames)
        bias_med = np.median(bias_frames, axis=0)
        return bias_med

def master_bias_header_cards(hdu, ci_extname):
    h = hdu.header
    h['FLAVOR'] = 'BIAS'
    h['EXTNAME'] = ci_extname

    return h

def write_master_bias():
    # loop over create_master_bias for all CI cameras except CIC
    # replace CIC bias with CIN bias because no non-simulated CIC lab data
    # is available

    outname = 'CI_master_bias.fits'
    outname = os.path.join(os.environ['CI_REDUCE_ETC'], outname)

    assert(not os.path.exists(outname))

    ci_extnames = common.valid_image_extname_list(fz=False)

    hdus = []
    for ci_extnum in range(len(ci_extnames)):
        ci_extname = common.ci_extnum_to_extname(ci_extnum, fz=False)
        print('Working on master bias for: ' + ci_extname)
        bias_image = \
          master_bias_1camera((ci_extname if (ci_extname != 'CIC') else 'CIN'))
        if len(hdus) == 0:
            hdu = fits.PrimaryHDU(bias_image)
        else:
            hdu = fits.ImageHDU(bias_image)
        hdu.header = master_bias_header_cards(hdu, ci_extname)

        hdus.append(hdu)

    hdul = fits.HDUList(hdus)

    hdul.writeto(outname)
