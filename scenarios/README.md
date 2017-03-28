### This folder contains configuration files for rally
    The reason to place it here is to remove dependency on rally stamples in upstream/rally


### Rally runner
    Clou99 uses rally tasks with specific "RPS" runnner.
    The "RPS" is stands for request per second. 
    To configure - just set the "rps" value.
        Note: At the current moment the rally_runner script will  set big enouth value for "times" param to use during run with disruption.
            In the future task runner will be tuned to wait for "abort" signal.
            Big enouth is like 1000 which means with 1 request per second runner will runned for 10000 seconds which enougth for long tests.

