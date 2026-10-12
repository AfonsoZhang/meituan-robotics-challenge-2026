source /driver_work/install/setup.bash
source /candidate-install/setup.bash
timeout --signal=TERM --kill-after=15 125 python3 /review-tools/probe_fake_tf.py /review-evidence/fake-tf
