"""Plot measured desired/actual TCP from a completed recording; no ROS required."""
import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'meituan-demo-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    data = np.genfromtxt(args.run/'tracking.csv', delimiter=',', names=True)
    if data.size < 2: raise ValueError('Insufficient tracking observations')
    summary = json.loads((args.run/'summary.json').read_text())
    fig, axes = plt.subplots(4,1,figsize=(11,8),sharex=True,layout='constrained')
    t = data['elapsed_s']
    for ax,key in zip(axes[:3],'xyz'):
        ax.plot(t,data[f'desired_tcp_{key}']*1000,label='Controller reference',lw=1.8)
        ax.plot(t,data[f'actual_tcp_{key}']*1000,label='Measured joints + nominal FK',lw=1.1,ls='--')
        ax.set_ylabel(f'{key.upper()} (mm)'); ax.grid(alpha=.25)
    axes[0].legend(loc='best',ncols=2)
    axes[3].plot(t,data['tcp_tracking_error_mm'],color='#b04a2e',lw=1.3)
    axes[3].set_ylabel('TCP error (mm)'); axes[3].set_xlabel('Simulation time since goal submission (s)')
    axes[3].grid(alpha=.25)
    fig.suptitle('S3 passive-hook simulation: controller reference vs measured TCP\n'
                 'Tracking error is not battery localization or placement error',fontsize=13)
    fig.savefig(args.run/'tracking.png',dpi=170)
    fig.savefig(args.run/'tracking.pdf')
    plt.close(fig)
    print('Saved tracking.png and tracking.pdf; run passed:',summary.get('passed'))


if __name__ == '__main__': main()
