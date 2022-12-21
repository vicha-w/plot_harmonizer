import numpy as np
import uproot
import yaml
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import mplhep as hep
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("yamlspec", \
    help="YAML file containing plots to be drawn.")
parser.add_argument("--colourspec", default="colours.yaml", \
    help="YAML file containing colour specifications. Default is colours.yaml. Mind the spelling!")
parser.add_argument("--propernamespec", default="propernames.yaml", \
    help="YAML file containing names used in plot legends. Default is propernames.yaml.")
parser.add_argument("--showonly", action="store_true", \
    help="Do not save file. Show only plots.")
parser.add_argument("--outputdir", \
    help="Directory to save figures. Default is the current directory.")

args = parser.parse_args()

with open(args.colourspec, 'r') as colorsfile:
    colors_keys = yaml.safe_load(colorsfile)
with open(args.propernamespec, 'r') as namesfile:
    propernames_keys = yaml.safe_load(namesfile)

with open(args.yamlspec, 'r') as yamlfile:
    yamlspec = yaml.safe_load(yamlfile)

plt.style.use(hep.style.CMS)

default_opts = {
    "outputdir": ".",
    "figsize": (10, 8),
    "mountainrange": False,
    "mountainrange_sum": False,
    "mainratio": False,
    "ratio": False,
    "ratiorange": [0, 2],
    "xrange": None,
    "yrange": None,
    "logy": False,
    "logy_legacy": False,
    "lumi": 138,
    "cmslabelmode": 2,
    "cmspadding": 0.05,
    "llabel": "Preliminary",
    "xlabel": "",
    "ylabel_main": "Events",
    "ylabel_ratio": "Data/Sim",
    "customticks": None,
    "ticks_size": 28,
    "ticks_rotation": 0,
    "whitespace": 0.25, 
    "legendcol": 1,
    "legendloc": "upper center",
    "legendanchor": [0.55, 1],
}

common_opts = yamlspec["common_opts"]

for plot in yamlspec["plots"]:
    print("-------------------------")
    print(f"Plotting {plot['outputname']}")
    if "total" not in [p["name"] for p in plot["processmap"]]:
        raise IndexError("Histogram total not specified in YAML specs.")
    if "data_obs" not in [p["name"] for p in plot["processmap"]]:
        raise IndexError("Histogram data_obs not specified in YAML specs.")
    opts = {}
    opts_keys = default_opts.keys()
    for key in opts_keys:
        if key not in plot.keys(): 
            if key in common_opts.keys(): opts[key] = common_opts[key]
            else: opts[key] = default_opts[key]
        else: opts[key] = plot[key]
    if args.outputdir: opts["outputdir"] = args.outputdir

    processhists = {}
    mcerr = []
    dataerr = []
    histbins = None
    delimiter_bins = None

    histfile = uproot.open(plot["file"])

    for process in plot["processmap"]:
        processhists[process["name"]] = []
        for histpath in process["histname"]:
            if type(histpath) == str:
                try:
                    histobj = histfile[histpath]
                    processhists[process["name"]].append(histobj.values())
                    if process["name"] == "data_obs": dataerr.append(histobj.errors())
                    elif process["name"] == "total": 
                        mcerr.append(histobj.errors())
                except Exception as e:
                    processhists[process["name"]].append([])
            elif type(histpath) == list:
                if not opts["mountainrange"]:
                    raise Exception("When mountainrange options is false, histname must be a list of strings, not *list of list* of strings!")
                opts["mountainrange_sum"] = True
                histcache = []
                mcerrcache = []
                dataerrcache = []
                for path in histpath:
                    try:
                        histobj = histfile[path]
                        histcache.append(histobj.values())
                        if process["name"] == "data_obs": dataerrcache.append(histobj.errors())
                        elif process["name"] == "total": 
                            mcerrcache.append(histobj.errors())
                    except Exception as e:
                        print(path, "not in histfile")
                        histcache.append([])
                processhists[process["name"]].append(histcache)
                if process["name"] == "total": mcerr.append(mcerrcache)
                if process["name"] == "data_obs": dataerr.append(dataerrcache)

            if not opts["mountainrange"]:
                if type(histbins) != list: 
                    if type(process["histname"]) == list: histbins = histfile[process["histname"][0]].axis().edges()
                    else: histbins = histfile[process["histname"]].axis().edges()
    
    print("-------------------------")
    print("Adjusting bins")
    if opts["mountainrange_sum"]:
        process_nbins = []
        final_bins = []
        for process in processhists.keys():
            for i in range(len(processhists[process])):
                highest_bins = max([len(hist) for hist in processhists[process][i]])
                for j in range(len(processhists[process][i])):
                    if len(processhists[process][i][j]) == 0:
                        processhists[process][i][j] = np.zeros(highest_bins)
                processhists[process][i] = np.sum(processhists[process][i], axis=0)
            process_nbins.append([len(hist) for hist in processhists[process]])

        for i in range(len(mcerr)):
            highest_bins = max([len(hist) for hist in mcerr[i]])
            for j in range(len(mcerr[i])):
                if len(mcerr[i][j]) == 0: 
                    mcerr[i][j] = np.zeros(highest_bins)
            for j in range(len(dataerr[i])):
                if len(dataerr[i][j]) == 0: 
                    dataerr[i][j] = np.zeros(highest_bins)
            mcerr[i] = np.sqrt(np.sum([err**2 for err in mcerr[i]], axis=0))
            dataerr[i] = np.sqrt(np.sum([err**2 for err in dataerr[i]], axis=0))
    if opts["mountainrange"]:
        process_nbins = []
        final_bins = []
        for process in processhists.keys():
            process_nbins.append([len(hist) for hist in processhists[process]])
        final_bins = np.max(np.array(process_nbins).transpose(), axis=1)
        for process in processhists.keys():
            for i in range(len(processhists[process])):
                if len(processhists[process][i]) == 0:
                    processhists[process][i] = np.zeros(final_bins[i])
        for i in range(len(processhists["total"])):
            if len(mcerr[i]) == 0:
                mcerr[i] = np.zeros(final_bins[i])

    if opts["mountainrange"]:
        histbins = range(len([item for sublist in processhists["data_obs"] for item in sublist])+1)
        mountainrange_nbins = [len(bins) for bins in processhists["data_obs"]]
        delimiter_bins = [0]
        for i in range(len(mountainrange_nbins)):
            delimiter_bins.append(delimiter_bins[-1] + mountainrange_nbins[i])
        for process in processhists.keys():
            processhists[process] = np.concatenate(processhists[process])
        mcerr = np.concatenate(mcerr)
        dataerr = np.concatenate(dataerr)
    else:
        for process in processhists.keys(): processhists[process] = np.sum(processhists[process], axis=0)
        mcerr = np.sqrt(np.sum([err**2 for err in mcerr], axis=0))
        dataerr = np.sqrt(np.sum([err**2 for err in dataerr], axis=0))

    if opts["mainratio"]:
        for process in plot["ordering"]:
            processhists[process] = processhists[process]/processhists["total"]*100
        
    print("-------------------------")
    print("Starting plot")

    print(processhists)

    fig = plt.figure(figsize=opts["figsize"], facecolor="white")
    if opts["ratio"] and (not opts["mainratio"]): 
        main_ax = plt.subplot2grid((5, 1), (0, 0), rowspan=4)
        ratio_ax = plt.subplot2grid((5, 1), (4, 0))
        fig.subplots_adjust(hspace=0)
    else: main_ax = fig.gca()
    baseline = np.zeros(processhists["data_obs"].shape)
    for process in plot["ordering"]:
        print("Plotting", process)
        main_ax.stairs(
            np.array(processhists[process])+baseline, 
            histbins,
            baseline=baseline,
            fill=True,
            label=propernames_keys[process]["propername"],
            facecolor=colors_keys[process]["color"]
        )
        baseline += np.array(processhists[process])

    if not opts["mainratio"]:
        print("Plotting postfit error")
        main_ax.stairs(
            mcerr+baseline,
            histbins,
            baseline=baseline - mcerr,
            edgecolor=None,
            facecolor="black",
            fill=False,
            label="Postfit unc.",
            hatch="///",
            linewidth=0,
            linestyle=None
        )

        print("Plotting data")
        main_ax.errorbar(
            [(histbins[i]+histbins[i+1])/2 for i in range(len(histbins)-1)], 
            np.array(processhists["data_obs"]),
            fmt='o',
            markersize=10, linewidth=2, capsize=5, capthick=2,
            color="black",
            label="Data",
            #xerr=[(histbins[i+1]-histbins[i])/2 for i in range(len(histbins)-1)], 
            yerr=np.array(dataerr)
        )

    if opts["ratio"] and (not opts["mainratio"]):
        print("Plotting ratio plots")
        ratio_ax.errorbar(
            [(histbins[i]+histbins[i+1])/2 for i in range(len(histbins)-1)], 
            np.array(processhists["data_obs"])/np.array(processhists["total"]),
            color="black", fmt='o',
            markersize=10, linewidth=2, capsize=5, capthick=2,
            #xerr=[(histbins[i+1]-histbins[i])/2 for i in range(len(histbins)-1)],
            yerr=np.array(dataerr)/np.array(processhists["total"])
        )
        ratio_ax.stairs(
            np.array(mcerr)/np.array(processhists["total"])+1, 
            histbins,
            baseline=1-np.array(mcerr)/np.array(processhists["total"]),
            edgecolor=None,
            facecolor="black",
            fill=False,
            label="Postfit error",
            hatch="///",
            linewidth=0,
            linestyle=None
        )
        ratio_ax.axhline(1, linestyle="dashed", color="black", linewidth=1)

    print("-------------------------")
    print("a e s t h e t i c s")

    exptext, explabel = hep.cms.label(
        llabel=opts["llabel"], 
        lumi=opts["lumi"], 
        ax=main_ax, 
        loc=opts["cmslabelmode"]
    )
    if "text" in plot.keys(): 
        main_ax.text(0.05, 0.70, plot["text"], transform=main_ax.transAxes, va='top')

    print(exptext)
    print(explabel)

    if opts["cmslabelmode"] == 2:
        yaxis_pos, xaxis_pos = main_ax.transAxes.transform((0, 1))
        cmstext_pos, _ = main_ax.transAxes.transform((opts["cmspadding"], 1))
        _, cmstext_ypos = main_ax.transAxes.inverted().transform((cmstext_pos, (xaxis_pos-(cmstext_pos-yaxis_pos))))
        print((opts["cmspadding"], cmstext_ypos))
        exptext.set_position((opts["cmspadding"], cmstext_ypos))
        explabel.set_position((opts["cmspadding"], cmstext_ypos-opts["cmspadding"]))

    if opts["mountainrange"]:
        main_ax.set_xlim(0, sum(mountainrange_nbins))
        main_ax.set_xticklabels([])
    else:
        if opts["xrange"] is not None:
            main_ax.set_xlim(opts["xrange"])
        else: main_ax.set_xlim(min(histbins), max(histbins))
        main_ax.yaxis.get_major_ticks()[0].set_visible(False)

    if opts["logy"]: main_ax.set_yscale("log")
    if opts["yrange"]: ymin, ymax = sorted(opts["yrange"])
    else: ymin, ymax = main_ax.get_ylim()
    print("ymin", ymin, np.log10(ymin) if opts["logy"] else "")
    print("ymax", ymax, np.log10(ymax) if opts["logy"] else "")
    print("opts['whitespace']", opts["whitespace"])
    if opts["logy"]: 
        if opts["logy_legacy"]: ymax = ymax*(10**(1/(1-opts["whitespace"])))
        else: ymax = ymin * (ymax/ymin)**(1/(1-opts["whitespace"]))
    else: ymax = ymin + (ymax-ymin)/(1-opts["whitespace"])
    #ymax = ymax*(10**(1/(1-opts["whitespace"])) if opts["logy"] else 1/(1-opts["whitespace"]))
    print("new ymax", ymax, np.log10(ymax) if opts["logy"] else "")
    main_ax.set_ylim((ymin, ymax))
    main_ax.set_ylabel(opts["ylabel_main"])
    main_ax.tick_params(axis='y', which='major', labelsize=opts["ticks_size"])

    if opts["ratio"] and (not opts["mainratio"]):
        if opts["customticks"]: 
            main_ax.set_xticks([pos for pos, _ in opts["customticks"]], minor=False)
            main_ax.set_xticks([], minor=True)
            ratio_ax.set_xticks(
                [pos for pos, _ in opts["customticks"]], 
                labels=[name for _, name in opts["customticks"]],
                minor=False
            )
            ratio_ax.set_xticks([], minor=True)
        ratio_ax.set_xlabel(opts["xlabel"])
        ratio_ax.set_ylabel(opts["ylabel_ratio"])
        ratio_ax.set_ylim(opts["ratiorange"])
        ratio_ax.tick_params(axis='x', which='major', labelsize=opts["ticks_size"], rotation=opts["ticks_rotation"])
        ratio_ax.tick_params(axis='y', which='major', labelsize=opts["ticks_size"])
        ratio_ax.set_yticks(opts["ratiorange"] + [1.])
        if opts["mountainrange"]: 
            ratio_ax.set_xticklabels([])
            ratio_ax.set_xlim(0, sum(mountainrange_nbins))
        else: 
            if opts["xrange"] is not None:
                ratio_ax.set_xlim(opts["xrange"])
            else: ratio_ax.set_xlim(min(histbins), max(histbins))
        main_ax.set_xticklabels([])
        fig.align_ylabels([main_ax, ratio_ax])
    else: 
        main_ax.set_xlabel(opts["xlabel"])
        if opts["customticks"]: 
            main_ax.set_xticks(
                [pos for pos, _ in opts["customticks"]], 
                labels=[name for _, name in opts["customticks"]]
            )
        main_ax.tick_params(axis='x', which='major', labelsize=opts["ticks_size"], rotation=opts["ticks_rotation"])

    if opts["mountainrange"]: 
        main_ax.vlines(delimiter_bins[1:-1], ymin, ymax, color="black")
        trans = mtransforms.blended_transform_factory(main_ax.transData, main_ax.transAxes)
        if "mountainrange_labels" in plot.keys():
            for i in range(len(delimiter_bins)-1):
                main_ax.text(
                    delimiter_bins[i+1]-0.5, 
                    1-0.05, 
                    plot["mountainrange_labels"][i], 
                    ha="right", va="top",
                    transform=trans, 
                    #rotation=-90,
                )
        if opts["ratio"] and (not opts["mainratio"]):
            ratio_ax.vlines(delimiter_bins[1:-1], ymin, ymax, color="black")

    handles, labels = main_ax.get_legend_handles_labels()
    order = [len(labels)-1] + list(range(len(labels)-3, -1, -1)) + [len(labels)-2]
    if opts["mountainrange"]: 
        main_ax.legend(
            [handles[idx] for idx in order],
            [labels[idx] for idx in order], 
            loc=opts["legendloc"], 
            bbox_to_anchor=opts["legendanchor"], 
            ncol=opts["legendcol"]
        )
    else: 
        main_ax.legend(
            [handles[idx] for idx in order],
            [labels[idx] for idx in order], 
            loc="upper right", 
            ncol=opts["legendcol"]
        )
    
    if args.showonly: fig.show()
    else:
        fig.savefig(opts["outputdir"] + '/' + plot["outputname"] + ".pdf", bbox_inches="tight")
        print("Saved", opts["outputdir"] + '/' + plot["outputname"] + ".pdf")
        fig.savefig(opts["outputdir"] + '/' + plot["outputname"] + ".png", bbox_inches="tight")
        print("Saved", opts["outputdir"] + '/' + plot["outputname"] + ".png")
    
    if args.showonly: continue
    print("-------------------------")
    print("Preparing HEPdata")

    hepdata_dict = {}
    hepdata_dict["independent_variables"] = []
    hepdata_dict["dependent_variables"] = []

    xaxis_dict = {}
    xaxis_dict["header"] = {"name": opts["xlabel"]}
    if "xunits" in opts.keys(): xaxis_dict["header"]["units"] = opts["xunits"]
    xaxis_dict["values"] = []
    print("histbins", histbins)
    for i in range(len(histbins)-1):
        xaxis_dict["values"].append({"low": float(histbins[i]), "high": float(histbins[i+1])})
    hepdata_dict["independent_variables"].append(xaxis_dict)

    for process in plot["ordering"]:
        processhist_dict = {"header": propernames_keys[process]["propername"]}
        processhist_dict["values"] = []
        print(f"processhists[{process}]", processhists[process])
        for bin in processhists[process]:
            processhist_dict["values"].append({"value": float(bin)})
        hepdata_dict["dependent_variables"].append(processhist_dict)

    postfithist_dict = {"header": "Total postfit"}
    postfithist_dict["values"] = []
    for i in range(len(processhists["total"])):
        postfithist_dict["values"].append(
            {
                "value": float(processhists["total"][i]), 
                "errors":
                {
                    "label": "total uncertainty", 
                    "symerror": float(mcerr[i])
                }
            }
        )
    hepdata_dict["dependent_variables"].append(postfithist_dict)

    datahist_dict = {"header": "Data"}
    datahist_dict["values"] = []
    for i in range(len(processhists["data_obs"])):
        datahist_dict["values"].append(
            {
                "value": float(processhists["data_obs"][i]), 
                "errors":
                {
                    "label": "total uncertainty", 
                    "symerror": float(dataerr[i])
                }
            }
        )
    hepdata_dict["dependent_variables"].append(datahist_dict)
    
    #print(hepdata_dict)
    with open(opts["outputdir"] + '/' + (plot["hepdataname"] if "hepdataname" in plot.keys() else plot["outputname"]) + ".yaml", 'w') as outyaml:
        yaml.dump(hepdata_dict, outyaml, encoding="utf-8")