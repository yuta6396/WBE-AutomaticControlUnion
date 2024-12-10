import os
import netCDF4
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import subprocess
# import GPy
# import GPyOpt
# from sklearn.linear_model import LinearRegression
import time
import scipy.optimize as opt
from skopt import gp_minimize
from skopt.space import Real,Integer
from skopt.plots import plot_convergence, plot_evaluations, plot_objective
import warnings



# 警告を抑制
warnings.filterwarnings('ignore', category=DeprecationWarning)

matplotlib.use('Agg')

nofpe = 2
fny = 2
fnx = 1
run_time = 20
loop = 0

varname = 'PREC'

init_file = "init_00000101-000000.000.pe######.nc"
sub_init_file = "0000/init_00000101-000000.000.pe######.nc"
org_file = "init_00000101-000000.000.pe######.org.nc"
history_file = "history.pe######.nc"
sub_history_file = "0000/history.pe######.nc"
restart_file = "restart_00000101-010000.000.pe000000.nc"

orgfile = f"history-{loop}.pe######.nc"
now_file = f"now.pe######.nc"
temp_file=f"temp.pe######.nc"
temp2_file=f"temp2.pe######.nc"
file_path= os.path.dirname(os.path.abspath(__file__))

gpyoptfile=f"gpyopt-{loop}.pe######.nc"


swarmsize = 10

sum_gpy=np.zeros(40)
sum_no=np.zeros(40)

n=10

T = 6

opt_num=3

maxiter = opt_num
w = 0.5  # 慣性重み
c1 = 2.0  # 認知パラメータ
c2 = 2.0  # 社会パラメータ
w_max = 0.9  # 初期慣性重み
w_min = 0.4  # 最終慣性重み

def predict(inputs):
    #inputs=[0, 0, 0]
    for pe in range(nofpe):
        org = org_file.replace('######', str(pe).zfill(6))
        init = init_file.replace('######', str(pe).zfill(6))
        subprocess.run(["cp", org, init])
        
    for pe in range(nofpe):
        history = history_file.replace('######', str(pe).zfill(6))
        history_path = file_path+'/'+history
        if (os.path.isfile(history_path)):
                    subprocess.run(["rm", history])
    control(inputs[0],inputs[1],inputs[2])
    result = subprocess.run(
        ["mpirun", "-n", "2", "./scale-rm", "run_R20kmDX500m.conf"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # time.sleep(0.1)
    print(result.stdout.decode())
    print(result.stderr.decode())
    
    result = 0
    
    for pe in range(nofpe):
        fiy, fix = np.unravel_index(pe, (fny, fnx))
        nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
        nt = nc.dimensions['time'].size
        nx = nc.dimensions['x'].size
        ny = nc.dimensions['y'].size
        nz = nc.dimensions['z'].size
        gx1 = nx * fix
        gx2 = nx * (fix + 1)
        gy1 = ny * fiy
        gy2 = ny * (fiy + 1)
        if(pe==0):
            dat = np.zeros((nt, nz, fny*ny, fnx*nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[varname][:]
        for y_i in range(40):
            for t_j in range(nt):
                if t_j > 0:
                    result += dat[t_j,0,y_i,0]*300
        
    print(f"Result {result}")
    # print(f"predict,loop={loop}")
    
    return result

def control(input1,input2,input3):
    
    global org_file
    print(f"control input1={input1},input2={input2},input3={input3}")
    for pe in range(nofpe):
        output_file = f"out-MOMY.pe######.nc"
        init_file = f"init_00000101-000000.000.pe######.nc"
        
        init = init_file.replace('######', str(pe).zfill(6))
        output = output_file.replace('######', str(pe).zfill(6))
        with netCDF4.Dataset(init) as src, netCDF4.Dataset(output, "w") as dst:
            dst.setncatts(src.__dict__)
            for name, dimension in src.dimensions.items():
                dst.createDimension(
                    name, (len(dimension) if not dimension.isunlimited() else None))
            for name, variable in src.variables.items():
                x = dst.createVariable(
                    name, variable.datatype, variable.dimensions)
                dst[name].setncatts(src[name].__dict__)
                if name == 'MOMY':
                    var = src[name][:]
                    if pe==1:
                        var[0, 0, 0] += input1  # (y,x,z)
                        var[1, 0, 0] += input2 
                        var[2, 0, 0] += input3
                            
                    dst[name][:] = var
                else:
                    dst[name][:] = src[name][:]
        subprocess.run(["cp", output, init ])
    return


def f(inputs):
    print(f"f_inputs{inputs}")
    
    # control(inputs)
    cost_sum = predict(inputs)
    print(f"Cost at input {inputs}: Cost_sum {cost_sum}")
    
    return cost_sum #n個の配列　jobごとのコスト関数が入ってる


def state_update():
    global loop,sum_gpy,sum_no
    orgfile = f"history-{loop}.pe######.nc"
    gpyoptfile=f"PSO-{loop}-MOMY-opt{opt_num}.pe######.nc"
    for pe in range(nofpe):
        history_file = "history.pe######.nc"
        history = history_file.replace('######', str(pe).zfill(6))
        history_path = file_path+'/'+history
        if (os.path.isfile(history_path)):
            subprocess.run(["rm", history])
    print(f"update_run_")
    subprocess.run(["mpirun", "-n", "2", "../../../../scale-rm", "run_R20kmDX500m.conf"])
    # time.sleep(0.1)

    for pe in range(nofpe):
        output = gpyoptfile.replace('######', str(pe).zfill(6))
        history = history_file.replace('######', str(pe).zfill(6))
        subprocess.run(["cp", history,output])


    for pe in range(nofpe):
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
        if(pe==0):
            dat = np.zeros((nt, nz, fny*ny, fnx*nx))
            odat = np.zeros((nt, nz, fny*ny, fnx*nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[varname][:]
        odat[:, 0, gy1:gy2, gx1:gx2] = onc[varname][:]
    for i in range(40):
        sum_gpy[i]+=dat[1, 0, i, 0]*3600
        sum_no[i]+=odat[1, 0, i, 0]*3600
    for i in range(nt):
            l1, l2 = 'no-control', 'under-control'
            c1, c2 = 'blue', 'green'
            xl = 'y'
            yl = 'PREC'
            plt.plot(dat[i, 0, :, 0], color=c2, label=l2)
            plt.plot(odat[i, 0, :, 0], color=c1, label=l1)
            plt.xlabel(xl)
            plt.ylabel(yl)
            plt.legend()
            dirname = f"PSO-MOMY-={opt_num}-input={input_size}-T={T}/"
            os.makedirs(dirname, exist_ok=True)
            filename = dirname + \
                f'sabun-MOMY-t={loop}.png'
            plt.ylim(0, 0.025)
            plt.savefig(filename)
            plt.clf()

    loop += 1
    return 

# 粒子の初期化
def initialize_particles(num_particles, bounds):
    particles = []
    for _ in range(num_particles):
        position = np.array([np.random.uniform(bound[0], bound[1]) for bound in bounds])
        velocity = np.array([np.random.uniform(-1, 1) for _ in bounds])
        particles.append({
            'position': position,
            'velocity': velocity,
            'best_position': position.copy(),
            'best_value': float('inf'),
            'value': float('inf')
        })
    return particles

# 速度の更新
def update_velocity(particle, global_best_position, w, c1, c2):
    r1 = np.random.random(len(particle['position']))
    r2 = np.random.random(len(particle['position']))
    cognitive = c1 * r1 * (particle['best_position'] - particle['position'])
    social = c2 * r2 * (global_best_position - particle['position'])
    particle['velocity'] = w * particle['velocity'] + cognitive + social

# 位置の更新
def update_position(particle, bounds):
    particle['position'] += particle['velocity']
    for i in range(len(particle['position'])):
        if particle['position'][i] < bounds[i][0]:
            particle['position'][i] = bounds[i][0]
        if particle['position'][i] > bounds[i][1]:
            particle['position'][i] = bounds[i][1]

# PSOアルゴリズムの実装
def PSO(objective_function, bounds, num_particles, num_iterations):
    particles = initialize_particles(num_particles, bounds)
    global_best_value = float('inf')
    global_best_position = np.array([np.random.uniform(bound[0], bound[1]) for bound in bounds])

    w = w_max      # 慣性係数
    c1 = 2.0      # 認知係数
    c2 = 2.0      # 社会係数

    result_value = np.zeros(num_iterations)
    flag_b = 0
    for iteration in range(num_iterations):
        w = w_max - (w_max - w_min)*(iteration+1)/(num_iterations)
        flag_s = 0
        # f_PSO.write(f'w={w}')
        # print(f'w={w}')
        for particle in particles:
            particle['value'] = objective_function(particle['position'])
            print(particle['value'])
            if particle['value'] < particle['best_value']:
                particle['best_value'] = particle['value']
                particle['best_position'] = particle['position'].copy()

            if particle['value'] < global_best_value:
                global_best_value = particle['value']
                global_best_position = particle['position'].copy()

            if flag_s == 0 :
                iteration_positions = particle['position'].copy()
                flag_s = 1
            else:
                iteration_positions = np.vstack((iteration_positions, particle['position'].copy()))
        if flag_b == 0:
            position_history = iteration_positions
            flag_b = 1
        else:
            position_history = np.vstack(((position_history, iteration_positions)))# イテレーションごとの位置を保存

        for particle in particles:
            update_velocity(particle, global_best_position, w, c1, c2)
            update_position(particle, bounds)

        result_value[iteration] = global_best_value
        print(f"Iteration {iteration + 1}/{num_iterations}, Best Value: {global_best_value}")
        
    formatted_data = '[' + ',\n '.join([str(list(row)) for row in position_history]) + ']'
    # f_PSO.write(f"\nposition_history={formatted_data}")
    return global_best_position,  result_value



input_size=30



# lb1=[-30]
# ub1=[30]
# lb2=[-30]
# ub2=[30]
# lb3=[-30]
# ub3=[30]

# lb=[-30]*3
# ub=[30]*3

bounds=[(-30,30)]*3
np.random.seed(0)

for pe in range(nofpe):
    org = org_file.replace('######', str(pe).zfill(6))
    init = init_file.replace('######', str(pe).zfill(6))
    subprocess.run(["cp", org, init])

start = time.time()
best_position, result_value  = PSO(f, bounds, swarmsize, opt_num)
end = time.time()

best_values = []
current_best = float('inf')

# random_samples1 = np.random.uniform(-30, 30, (swarmsize,1))
# random_samples2 = np.random.uniform(-30, 30, (swarmsize,1))
# random_samples3 = np.random.uniform(-30, 30, (swarmsize,1))

#     # 各サンプルで目的関数を評価
# combined_samples = np.concatenate((random_samples1, random_samples2,random_samples3), axis=1)
# positions = combined_samples

for pe in range(nofpe):
    org = org_file.replace('######', str(pe).zfill(6))
    init = init_file.replace('######', str(pe).zfill(6))
    subprocess.run(["cp", org, init])

print(best_position)
control(best_position[0],best_position[1],best_position[2])

state_update()
print(f"loop={loop}")


time_diff = end - start
print(f'実行時間{time_diff}')

print(f"sum_gpy={sum_gpy}")


no=0
gpy=0
for i in range(40):
    no+=sum_no[i]
    gpy+=sum_gpy[i]

print(f"input={best_position}")
print(f"PSO={gpy}")
print(f"change%={(no-gpy)/no*100}%")
print(f"%={(gpy)/no*100}%")