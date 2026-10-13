import io,json,subprocess,sys,tarfile,time
from pathlib import Path

run=Path(json.loads(Path('.agents/webui-p2-current.json').read_text())['run'])
docker='/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe'
container='mtc-webui-p2-20261013'
name,kind,script=sys.argv[1:4]
if kind=='copy':
    subprocess.run([docker,'exec',container,'mkdir','-p','/ui-src','/p2-evidence'],check=True)
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as archive:
        for path in Path('webui').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                archive.add(path,arcname=str(path),recursive=False)
    subprocess.run([docker,'exec','-i',container,'tar','--no-same-owner','-xf','-','-C','/ui-src'],input=buffer.getvalue(),check=True)
    print('Copied current Web UI source')
    raise SystemExit(0)
path=run/'logs'/(name+'.log')
assert not path.exists(),path
env='source /opt/ros/jazzy/setup.bash; source /work/install/setup.bash; export PYTHONPATH=/ui-src:$PYTHONPATH ROS_DOMAIN_ID=94 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_LOG_DIR=/p2-evidence/roslogs; unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI; cd /ui-src; '
argv=[docker,'exec',container,'bash','-c',env+script] if kind=='ros' else ['bash','-c',script]
record=dict(argv=argv,started_at=time.time())
with path.open('w') as output:
    result=subprocess.run(argv,stdout=output,stderr=subprocess.STDOUT,timeout=180)
record.update(exit_code=result.returncode,finished_at=time.time())
path.with_suffix('.command.json').write_text(json.dumps(record,indent=2)+'\n')
print(path,result.returncode)
print(path.read_text()[-9000:])
raise SystemExit(result.returncode)
