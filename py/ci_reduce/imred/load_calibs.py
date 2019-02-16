import ci_reduce.common as common
import astropy.io.fits as fits
import os

def read_bias_image(ci_extname):
    assert(common.is_valid_extname(ci_extname))

    par = common.ci_misc_params()
    bias_fname = os.path.join(os.environ[par['etc_env_var']], \
                              par['master_bias_filename'])

    print('Attempting to read master bias : ' + bias_fname + 
          ', extension name : ' + ci_extname)

    assert(os.path.exists(bias_fname))

    bias = fits.getdata(bias_fname, extname=ci_extname)

    return bias

def read_flat_image(ci_extname):
    # at some point should add option to return master flat's
    # inverse variance as well
    assert(common.is_valid_extname(ci_extname))

    par = common.ci_misc_params()
    flat_fname = os.path.join(os.environ[par['etc_env_var']], \
                              par['master_flat_filename'])

    print('Attempting to read master flat : ' + flat_fname + 
          ', extension name : ' + ci_extname)

    assert(os.path.exists(flat_fname))

    flat = fits.getdata(flat_fname, extname=ci_extname)

    return flat
