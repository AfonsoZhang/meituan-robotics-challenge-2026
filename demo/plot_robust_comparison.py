"""Plot the actual frozen 2 Nm comparison, including the gain-matched control."""
import argparse,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/meituan-robust-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from metrics import Kinematics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained')
    for mode,label,color,style in [('pd','Gravity + PD','#aa5533','-'),('smc','Gravity + PD + sliding','#136b91','-'),('pd_matched','Gain-matched PD','#6b6b6b','--')]:
        run=args.root/('2nm-'+mode)
        state=np.genfromtxt(run/'tracking.csv',delimiter=',',names=True)
        a=np.genfromtxt(run/'effort-audit.csv',delimiter=',',names=True)
        t=a['sim_s']-(state['sim_s'][0]-state['elapsed_s'][0])
        kin=Kinematics(run/'robot.urdf')
        actual=np.column_stack([a['actual_'+str(i)] for i in range(6)])
        desired=np.column_stack([a['desired_'+str(i)] for i in range(6)])
        tcp=np.array([np.linalg.norm(kin.tcp(q)-kin.tcp(qd))*1000 for q,qd in zip(actual,desired)])
        for ax,y in zip(axes,[(actual[:,1]-desired[:,1])*1000,tcp,a['applied_1']]):
            ax.plot(t,y,label=label,color=color,ls=style,lw=1.2)
    for ax in axes:
        ax.axvspan(8,10,color='#e4ad44',alpha=.2)
        ax.axvspan(16,18,color='#e4ad44',alpha=.2)
        ax.grid(alpha=.25);ax.set_xlim(0,24)
    axes[0].legend(ncols=3,fontsize=9)
    axes[0].set_ylabel('Upper-arm error (mrad)');axes[1].set_ylabel('TCP tracking error (mm)')
    axes[2].set_ylabel('Command torque (Nm)');axes[2].set_xlabel('Simulation time from reference submission (s)')
    fig.suptitle('Gazebo effort control: external upper-arm torque +2 / -2 Nm\nSliding feedback overlaps gain-matched PD in this boundary-layer experiment')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output.with_suffix('.png'),dpi=160);fig.savefig(args.output.with_suffix('.pdf'))
