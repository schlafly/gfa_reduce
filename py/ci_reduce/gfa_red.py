#!/usr/bin/env python

import argparse
import os
import ci_reduce.io as io
from datetime import datetime
import ci_reduce.analysis.util as util
import ci_reduce.common as common
import ci_reduce.analysis.recalib_astrom as wcs

if __name__ == "__main__":
    descr = 'run full gfa_reduce pipeline on a GFA exposure'
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('fname_in', type=str, nargs=1)

    parser.add_argument('--outdir', default=None, type=str,
                        help='directory to write outputs in')

    parser.add_argument('--careful_sky', default=False, action='store_true',
        help='use image segmentation when deriving sky quantities')

    parser.add_argument('--no_cataloging', default=False, action='store_true', 
        help='reduce image without cataloging sources')

    parser.add_argument('--no_gaia_xmatch', default=False, action='store_true',
        help='skip Gaia cross-match')

    parser.add_argument('--cube_index', default=None, type=int,
                        help='guide cube index')

    parser.add_argument('--skip_image_outputs', default=False,
                        action='store_true',
                        help='skip writing of full-frame image outputs')
    
    args = parser.parse_args()

    print('Starting GFA reduction pipeline at: ' + str(datetime.utcnow()) + 
          ' UTC')

    fname_in = args.fname_in[0]
    cube_index = args.cube_index
    
    write_outputs = (args.outdir is not None)

    assert(os.path.exists(fname_in))

    gitrev = io.retrieve_git_rev()

    if write_outputs:
        outdir = args.outdir
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        # fail if ANY of expected outputs already exist
        io.check_image_level_outputs_exist(outdir, fname_in, gzip=True,
                                           cube_index=cube_index)

    exp = io.load_exposure(fname_in, cube_index=cube_index)

    print('Attempting to compute basic statistics of raw pixel data')
    imstats = io.gather_pixel_stats(exp)

    # create data quality bitmasks
    exp.create_all_bitmasks()

    # go from "raw" images to "reduced" images
    exp.calibrate_pixels()

    # calculate sky brightness in mag per sq asec
    exp.estimate_all_sky_mags(careful_sky=args.careful_sky)
    exp.estimate_all_sky_sigmas(careful_sky=args.careful_sky)

    par = common.ci_misc_params()

    if not args.no_cataloging:
        catalogs = exp.all_source_catalogs()

        for extname, cat in catalogs.items():
            if cat is not None:
                util.create_det_ids(cat, extname, fname_in,
                                    cube_index=cube_index)

        # reformat the output catalogs into a single merged astropy Table
        catalog = io.combine_per_camera_catalogs(catalogs)

        # run astrometric recalibration
        print('Attempting astrometric recalibration relative to Gaia DR2')
        astr = wcs.recalib_astrom(catalog, fname_in)
        exp.update_wcs(astr)
        exp.recompute_catalog_radec(catalog)
        
        if (not args.no_gaia_xmatch) and (par['gaia_env_var'] in os.environ):
            print('Attempting to identify Gaia cross-matches')
            catalog = io.append_gaia_crossmatches(catalog)
        
    # try to write image-level outputs if outdir is specified

    if write_outputs:
        if not args.skip_image_outputs:
            print('Attempting to write image-level outputs to directory : ' + 
                  outdir)
            # could add command line arg for turning off gzip compression
            io.write_image_level_outputs(exp, outdir, fname_in, gzip=True,
                                         cube_index=cube_index)

        if not args.no_cataloging:
            io.write_exposure_source_catalog(catalog, outdir, fname_in,
                                             cube_index=cube_index)
        # make this work correctly in the case that --no_cataloging is set
        io.write_ccds_table(imstats, catalog, exp, outdir, fname_in,
                            cube_index=cube_index)

    print('Successfully finished reducing ' + fname_in)

    print('GFA reduction pipeline completed at: ' + str(datetime.utcnow()) + 
          ' UTC')