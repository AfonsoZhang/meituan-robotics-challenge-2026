"""Independent gravity validation by finite differences of URDF potential energy."""
import xml.etree.ElementTree as ET
import numpy as np
from metrics import rpy_matrix, JOINTS


def gravity_from_potential(urdf,q):
    root=ET.parse(urdf).getroot()
    children={j.find('child').get('link'):j for j in root.findall('joint')}
    links={l.get('name'):l for l in root.findall('link')}
    def vector(element,key,default='0 0 0'):
        return np.fromstring(element.get(key,default),sep=' ') if element is not None else np.zeros(3)
    def potential(angles):
        cache={}
        values=dict(zip(JOINTS,angles))
        def pose(name):
            if name in cache:return cache[name]
            if name not in children:result=(np.zeros(3),np.eye(3))
            else:
                joint=children[name];p,R=pose(joint.find('parent').get('link'));origin=joint.find('origin')
                p=p+R@vector(origin,'xyz');R=R@rpy_matrix(*vector(origin,'rpy'))
                if joint.get('type') in ('revolute','continuous'):
                    axis=vector(joint.find('axis'),'xyz','1 0 0');axis/=np.linalg.norm(axis)
                    a=values[joint.get('name')];K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
                    R=R@(np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K))
                result=(p,R)
            cache[name]=result;return result
        energy=0.
        for name,link in links.items():
            inertial=link.find('inertial')
            if inertial is None:continue
            mass=float(inertial.find('mass').get('value'));p,R=pose(name)
            energy+=mass*9.81*(p+R@vector(inertial.find('origin'),'xyz'))[2]
        return energy
    step=1e-6;q=np.array(q,dtype=float)
    return np.array([(potential(q+np.eye(6)[i]*step)-potential(q-np.eye(6)[i]*step))/(2*step) for i in range(6)])

if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);args=p.parse_args()
    tracking=np.genfromtxt(args.run/'tracking.csv',delimiter=',',names=True)
    audit=np.genfromtxt(args.run/'effort-audit.csv',delimiter=',',names=True)
    errors=[]
    for row in tracking[::20]:
        q=[row['actual_'+j] for j in JOINTS]
        reference=gravity_from_potential(args.run/'robot.urdf',q)
        measured=audit[np.argmin(abs(audit['sim_s']-row['sim_s']))]
        errors.append(float(np.max(abs(reference-[measured['gravity_'+str(i)] for i in range(6)]))))
    result=dict(samples=len(errors),max_joint_gravity_discrepancy_nm=max(errors),
                note='Finite-difference potential vs C++ Jacobian gravity; nearest audit timestamp, not exactly synchronized.')
    print(json.dumps(result,indent=2))
    if max(errors)>.02:raise SystemExit(1)
