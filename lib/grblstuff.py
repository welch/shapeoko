#
# utilities for talking to grbl running on an arduino
# (https://github.com/grbl/grbl/wiki)
#
# you need the pyserial module installed so we can speak to the usb
# serial device.
#
import sys
import time
import glob
from logging import getLogger, DEBUG, INFO, WARN, basicConfig
def log(logger='grblstuff'):
    return getLogger(logger)

try:
    import serial
except ImportError:
    print "You must install the pyserial module (sorry!)"
    print "http://pyserial.sourceforge.net/pyserial.html"
    sys.exit()

def setup_logging(info=False, debug=False, path=None, logstream=sys.stderr):
    """
    initialize the python logger at proper level writing to the given
    path or open file stream.
    """
    level = (DEBUG if debug else INFO if info else WARN)
    if path:
        logstream = open(path, "w")
    basicConfig(
        stream=logstream, level=level,
        format='%(asctime)s [%(name)s %(levelname)s] %(message)s',
        datefmt='%b-%d %H:%M:%S')

class GRBLException(Exception):
    pass

def open_grbl(serial_dev_pattern=None):
    """
    find the grbl usb modem device and return an open filehandle
    """
    serial_dev_pattern = serial_dev_pattern or "/dev/tty.usbmodem*"
    grbl_paths = glob.glob(serial_dev_pattern)
    if not grbl_paths:
        raise GRBLException("Can't find serial device, is the grbl plugged in?")
    log().info("connecting to grbl via %s" % grbl_paths[0])
    return serial.Serial(grbl_paths[0], 9600, timeout=5, dsrdtr=True)

def reset_grbl_connection(serial_dev_pattern=None):
    """
    assert DTR to shake the grbl serial line out of any lethargy
    """
    log().info("resetting grbl connection")
    try:
        grbl = open_grbl(serial_dev_pattern)
    except GRBLException, e:
        log().error(e)
        return
    grbl.setDTR(True)
    time.sleep(1)
    grbl.setDTR(False)
    grbl.close()

def read_response(grbl, until="ok", raise_errors=False):
    """
    read lines from the grbl until the expected matching line appears
    (usually "ok"), or just the first line if until is None. Return
    all lines joined by \n. If an error is encountered, log it and
    return any output accumulated prior to the error (probably nothing),
    or if raise_errors, raise a GRBLException with the error text.
    """
    result = []
    while True:
        line = grbl.readline().strip()
        if line.startswith("error:"):
            if raise_errors:
                raise GRBLException(line)
            log("grbl").error(line[6:])
            break
        result.append(line)
        if line==until or until==None:
            break
    return '\n'.join(result)

def do_command(grbl, command, wait=False):
    """
    send the command to grbl, read the response and return it.
    if wait=True, wait for the stepper motion to complete before returning.
    """
    command = command.strip()
    log().info(">>>> " + command)
    if not command or command[0] == '(':
        return
    grbl.write(command+'\n')
    response = read_response(grbl)
    if wait:
        wait_motion(grbl)
    log('grbl').info("<<<< "+response)
    return response
    
def wait_motion(grbl):
    """
    force grbl to wait until all motion is complete. 
    """
    #
    # the gcode dwell command as implemented by grbl includes a
    # stepper-motor sync prior to beginning the dwell countdown.
    # use it to force a pause-until-caught-up.
    do_command(grbl, "G4 P0") 

def set_home(grbl):
    """
    establish current location as the new zero
    """
    log().info("current position will be zero")
    do_command(grbl, "G92 x0 y0 z0")

def go_home(grbl):
    """
    move to 0,0,0
    """
    do_command(grbl, "G0 x0 y0 z0")
    
def pen_up(grbl):
    """
    raise the pen a bit
    """
    do_command(grbl, "G01 Z10")
    
def hello_grbl(serial_dev_pattern=None, conf_path=None):
    """
    find the grbl, wake it up, and send it any configuration specified
    in the config path.  return a handle to the grbl session.
    """
    try:
        grbl = open_grbl(serial_dev_pattern)
    except GRBLException, e:
        log().error(e)
        return None
    grbl.write("\r\n")
    time.sleep(2) # wake up!
    grbl.flushInput()
    if conf_path:
        log().info("loading grbl conf from %s" % conf_path)
        for line in open(conf_path):
            do_command(grbl, line)
    return grbl

