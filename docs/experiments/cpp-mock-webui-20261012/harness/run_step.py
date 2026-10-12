import datetime,json,os,pathlib,subprocess,sys,time
p=pathlib.Path(__file__).resolve().parent
name,kind,script=sys.argv[1:4]
record={'name':name,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':kind,'script':script}
log=p/'logs'/f'{name}.log'
if log.exists():raise SystemExit('Refusing overwrite '+str(log))
if kind=='ros':
 env='source /opt/ros/jazzy/setup.bash; source /candidate-install/setup.bash; if [ -f /integration-install/setup.bash ]; then source /integration-install/setup.bash; fi; unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI; export ROS_DOMAIN_ID=161 RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/integration-evidence/roslogs; '
 argv=['docker','exec','mtc-cpp-webui-review','bash','-c',env+script]
else:argv=['bash','-c',script]
record['argv']=argv
(p/'evidence'/f'{name}-command.json').write_text(json.dumps(record,indent=2)+'\n')
with log.open('wb') as stream:
 proc=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=proc.wait(timeout=1500)
 except subprocess.TimeoutExpired:
  import signal
  os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=15);rc=124
  if kind=='ros':subprocess.run(['docker','stop','--time','5','mtc-cpp-webui-review'],stdout=stream,stderr=stream)
record.update(exit_code=rc,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(p/'evidence'/f'{name}-command.json').write_text(json.dumps(record,indent=2)+'\n')
print(name,rc,flush=True)
raise SystemExit(rc)
