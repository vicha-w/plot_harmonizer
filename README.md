`plot_harmonizer.py`
---
Plotting script accepting easy YAML inputs, designed for TOP-21-005

## Requirements
- [numpy](https://numpy.org/)
- [uproot](https://github.com/scikit-hep/uproot5)
- [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [matplotlib](https://matplotlib.org/)
- [mplhep](https://github.com/scikit-hep/mplhep)

## Usage
```bash
python3 plot_harmonizer.py <PLOT_FILE> --colourspec <COLOURSPEC_FILE> --propernamespec --outputdir <OUTPUT_DIR> --showonly
```
- `--colourspec`: YAML file specifying colour scheme. Default file name is `colourspec.yaml`. (Mind the spelling!)
- `--propernamespec`: YAML file specifying "proper names", or names of processes appearing on legends in the plots. Default file name is `propernames.yaml`.
- `--outputdir`: Output directory. Default is current directory.
- `--showonly`: Show plots directly on new window. Do not save plots.

This script generates two plot files in PDF and PNG format (unless `--showonly` option is present) and one hepdata YAML file per one plot.

## Plotting file YAML specs
The file structure is as follows:
- `common_opts`: Common options to be applied to all plots.
- `plots`: Details and specific options for each plot. Requires the following options.
    - `outputname`: Output file name
    - `file`: Input ROOT file
    - `ordering`: Order of histograms to be arranged as a stack. Must be written as a list.
    - `processmap`: Mapping of each process to the correct histogram. Each object in the list must contain two attributes:
        - `name`: Name of the process
        - `histname`: Name of histogram in ROOT input file (as specified in `file`). Can be in the following format:
            - List of one or more histograms = one histogram combined if `mountainrange` option is `False`, or a mountain range of histograms if `mountainrange` option is `True`
            - List of list of one or more histograms = mountain range plot, each element of list refers to one or more histograms, combined in the same way as list of one or more histograms. Requires `mountainrange` option.
    - `hepdataname`: Name of hepdata file for the plot.

Options specified in `plots` will be used first. If the option is not available in plot object, it will fall back to `common_opts`. If the option is still not available, it will fall back to default options specified in code. 

Details of additional options are as follows:
- `outputdir`: Output directory for each plot. `--outputdir` option in Terminal command overrides this option. Default is `.`
- `figsize`: Figure size as specified in `plt.figure()`. Default is `(10, 8)`
- `mountainrange`: Make this plot in mountainrange format. Default is `False`
- `mainratio`: Make ratio plot as main plot, with y-axis as percentage. Default is `False`
- `ratio`: Add ratio plot at the bottom of main plot. Default is `False`
- `ratiorange`: Range of ratio plot. Default is `[0, 2]`
- `yrange`: Range of main y-axis _before allocating whitespace, as in `whitespace` option_. Default is `None`
- `logy`: Set log scale on y-axis. Default is `False`
- `logy_legacy`: Legacy mode for y-axis maximum calculation. Made for compatibility with main paper plots before a bug fix in maximum y-axis value in log scale. Default is `False`
- `lumi`: Luminosity size as specified in `mplhep.cms.label(lumi=lumi)`. Default is `138`
- `cmslabelmode`: CMS label mode as specified in `mplhep.cms.label(loc=cmslabelmode)`. Default is `2`
- `cmspadding`: Padding of CMS label in plot if `cmslabelmode` is `2`, designed to place CMS labels with equal spacing from top and left border. Default is `0.05`
- `llabel`: Additional text for CMS label, as specified in `mplhep.cms.label(llabel=llabel)`. Default is `Preliminary`
- `xlabel`: x-axis label. Default is `""`
- `ylabel_main`: y-axis label for main plot. Default is `"Events"`
- `ylabel_ratio`: y-axis label for ratio plot. Default is `"Data/Sim"`
- `customticks`: Custom ticks positions. Must be in the form of a list of [position, name]. Default is `None`
- `ticks_size`: Size of ticks in all plots. Default is `28`
- `ticks_rotation`: Ticks rotation in x-axis. Default is `0`
- `whtiespace`: Whitespace allocation in the plot. Default is `0.25`
- `legendcol`: Number of columns in legend. Default is `1`
- `legendloc`: Legend location as specified in `plt.legend(loc=legendloc)`. Default is `upper center`
- `legendanchor`: Legend bbox anchor as specified in `plt.legend(bbox_to_anchor=legendanchor)`. Requires `mountainrange` option to be `True`. Default is `[0.55, 1]`

## Colour spec and proper name spec YAML file
Colour spec file is simply a dictionary of colours to be used in plots. The structure is as follows:
```yaml
<PROCESS_NAME>:
    colour: <COLOUR>
```
Colour hex code is recommended, but matplotlib colour names can also be used. Process name must be the same as specified in plotting spec file.

Proper name spec file is structured in the same way as follows:
```yaml
<PROCESS_NAME>:
    propername: <NAME_USED_IN_LEGENDS>
```

## Example files
- `plots_sl.yaml`, `plots_osdl.yaml`, `plots_allhad.yaml` plotting YAML files
- `colours_elbphilharmonie_v2.yaml` colour spec YAML file
- `propernames.yaml` proper name spec YAML file