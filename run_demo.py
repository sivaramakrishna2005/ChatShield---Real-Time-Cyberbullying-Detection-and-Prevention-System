"""run_demo.py
Starts the prediction Flask service and the socket chat server, then opens the GUI client.

Usage:
  python run_demo.py        # starts servers and opens the GUI (requires a desktop session)
  python run_demo.py --no-gui  # starts servers and runs a small smoke test, then exits

This single-file launcher uses relative paths and assumes the model/vocab/stopwords
pickles exist in `service_testing/` and `Safe_Chat/` as in the repository.
"""
import os
import sys
import threading
import time
import socket
import traceback

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(ROOT)

def check_files():
    required = [
        os.path.join(ROOT, 'service_testing', 'LinearSVC.pkl'),
        os.path.join(ROOT, 'service_testing', 'tfidf_vector_vocabulary.pkl'),
        os.path.join(ROOT, 'service_testing', 'stopwords.txt'),
        os.path.join(ROOT, 'Safe_Chat', 'LinearSVC.pkl'),
        os.path.join(ROOT, 'Safe_Chat', 'tfidf_vector_vocabulary.pkl'),
        os.path.join(ROOT, 'Safe_Chat', 'stopwords.txt'),
    ]
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        print('ERROR: The following required files are missing:')
        for p in missing:
            print('  -', os.path.relpath(p, ROOT))
        print('\nPlease generate the .pkl files by running the notebooks in `Code/` or copy them into the folders.')
        return False
    return True

def start_flask():
    try:
        print('Starting Flask prediction service (http://127.0.0.1:5000) ...')
        svc = __import__('service_testing.app', fromlist=['app'])
        flask_app = svc.app
        # run in a thread; disable reloader and debugger for threaded launch
        t = threading.Thread(target=lambda: flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False), daemon=True)
        t.start()
        return t
    except Exception:
        print('Failed to start Flask app:')
        traceback.print_exc()
        return None

def start_chat_server():
    try:
        print('Starting socket chat server (127.0.0.1:12345) ...')
        server_mod = __import__('Safe_Chat.server', fromlist=['Server'])
        Server = server_mod.Server
        server = Server()
        t = threading.Thread(target=lambda: server.accept_connections('127.0.0.1', 12345), daemon=True)
        t.start()
        return server, t
    except Exception:
        print('Failed to start chat server:')
        traceback.print_exc()
        return None, None

def run_smoke_tests():
    print('\nRunning smoke tests...')
    time.sleep(1.0)
    # Test Flask endpoint
    try:
        from urllib import request, parse
        data = parse.urlencode({'Body':'hi','From':'demo'}).encode()
        resp = request.urlopen('http://127.0.0.1:5000/testing', data=data, timeout=5)
        body = resp.read().decode()
        print('Flask /testing response for "hi":', body)
    except Exception as e:
        print('Flask endpoint test failed:')
        traceback.print_exc()

    # Test socket server accepts a connection and responds to initial handshake
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 12345))
        # send user id and room id as the client.py expects
        s.send(str.encode('demo_user'))
        time.sleep(0.1)
        s.send(str.encode('demo_room'))
        # receive welcome/new group message
        reply = s.recv(1024).decode()
        print('Chat server initial reply:', reply)
        s.close()
    except Exception:
        print('Chat server test failed:')
        traceback.print_exc()

def launch_gui_clients(num_clients=2):
    """Launch multiple GUI client processes (each runs Safe_Chat/client_GUI.py).
    We spawn separate processes so each has its own Tk mainloop.
    """
    import subprocess
    clients = []
    python_exec = sys.executable or 'python'
    for i in range(num_clients):
        try:
            print(f'Launching GUI client #{i+1}...')
            p = subprocess.Popen([python_exec, os.path.join(ROOT, 'Safe_Chat', 'client_GUI.py')])
            clients.append(p)
        except Exception:
            print(f'Failed to launch GUI client #{i+1}:')
            traceback.print_exc()
    return clients

def main():
    no_gui = '--no-gui' in sys.argv or '-n' in sys.argv

    ok = check_files()
    if not ok:
        sys.exit(1)

    ft = start_flask()
    server, st = start_chat_server()

    # give servers a moment to start
    time.sleep(1.0)

    if no_gui:
        run_smoke_tests()
        print('\nServers are running in background threads (no GUI). Exiting demo runner.')
        return

    # Launch two GUI clients as separate processes (so both windows appear)
    clients = launch_gui_clients(num_clients=2)
    # Wait for GUI processes to exit (block here). If you prefer to exit the demo runner
    # but keep GUIs running, remove the following join loop.
    try:
        for p in clients:
            if p:
                p.wait()
    except KeyboardInterrupt:
        print('\nInterrupted; terminating GUI clients...')
        for p in clients:
            try:
                p.terminate()
            except Exception:
                pass

if __name__ == '__main__':
    main()
