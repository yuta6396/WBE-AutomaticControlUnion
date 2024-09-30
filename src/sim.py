def sim(input):
    global sum_co,sum_no, input_var, num_input_grid
    for pe in range(nofpe):
        output_file = f"out-{input_var}.pe######.nc"
        # input file
        init = init_file.replace('######', str(pe).zfill(6))
        org = org_file.replace('######', str(pe).zfill(6))
        history = history_file.replace('######', str(pe).zfill(6))
        output = output_file.replace('######', str(pe).zfill(6))
        history_path = file_path+'/'+history
        if(os.path.isfile(history_path)):
            subprocess.run(["rm",history])
        subprocess.run(["cp", org, init]) #初期化
        with netCDF4.Dataset(init) as src, netCDF4.Dataset(output, "w") as dst:
            # copy global attributes all at once via dictionary
            dst.setncatts(src.__dict__)
            # copy dimensions
            for name, dimension in src.dimensions.items():
                dst.createDimension(
                    name, (len(dimension) if not dimension.isunlimited() else None))
            # copy all file data except for the excluded
            for name, variable in src.variables.items():
                x = dst.createVariable(
                    name, variable.datatype, variable.dimensions)
                # copy variable attributes all at once via dictionary
                dst[name].setncatts(src[name].__dict__)
                if name == input_var:
                    var = src[name][:]
                    if pe ==1:
                        for Ygrid_i in range(num_input_grid):
                            var[Ygrid_i, 0, 0] += input[Ygrid_i]  # (y,x,z)
                    dst[name][:] = var
                else:
                    # dst[name][:] = hfi[name][:] #(y,x,z)=(time,z,y,x)
                    dst[name][:] = src[name][:]
        subprocess.run(["cp", output, init])

    subprocess.run(["mpirun", "-n", "2", "./scale-rm", "run_R20kmDX500m.conf"])

    # time.sleep(0.3)
    for pe in range(nofpe):
        gpyopt = gpyoptfile.replace('######', str(pe).zfill(6))
        history = history_file.replace('######', str(pe).zfill(6))
        subprocess.run(["cp", history,gpyopt])
    for pe in range(nofpe):  # history処理
        fiy, fix = np.unravel_index(pe, (fny, fnx))
        nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
        onc = netCDF4.Dataset(orgfile.replace('######', str(pe).zfill(6)))
        nt = nc.dimensions['time'].size
        nx = nc.dimensions['x'].size
        ny = nc.dimensions['y'].size
        nz = nc.dimensions['z'].size
        gx1 = nx * fix
        gx2 = nx * (fix + 1)
        gy1 = ny * fiy
        gy2 = ny * (fiy + 1)
        if pe == 0:
            dat = np.zeros((nt, nz, fny*ny, fnx*nx))
            odat = np.zeros((nt, nz, fny*ny, fnx*nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[varname][:]
        odat[:, 0, gy1:gy2, gx1:gx2] = onc[varname][:]

    result = 0
    for i in range(40):
        sum_co[i]+=dat[1,0,i,0]*3600
        sum_no[i]+=odat[1,0,i,0]*3600
        result += dat[1,0,i,0]*3600

    result = result/40

    cost =coefficient_accumulated*np.tanh( coefficient_tanh*(result - AccumulatedPREC_NoControl*target_ratio))
    for j in range(num_input_grid):
        cost += abs(input[j])
    return cost
