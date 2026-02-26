import os
import sys
import threading
import time


RPYC_PORT = int(os.environ.get('RPYC_PORT', 28946))

import rpyc_reverse


def setup_rpyc_service(client_id):
    print(f"RPyC: Setting up reverse connection service")
    rc = rpyc_reverse.setup_reverse_connection(client_id)
    print(f"RPyC: Service configured")
    return rc


def stop_rpyc_service():
    rpyc_reverse.stop_reverse_connection()
    print(f"RPyC: Service stopped")
