#!/bin/bash

cmd=$1

case "$cmd" in
    start)
        echo "Starting backend servers..."

        nohup python3 backend.py 8004 server-1 > server1.log 2>&1 &
        echo $! > server1.pid

        nohup python3 backend.py 8005 server-2 > server2.log 2>&1 &
        echo $! > server2.pid

        nohup python3 backend.py 8006 server-3 > server3.log 2>&1 &
        echo $! > server3.pid

        echo "Starting load balancer..."

        nohup python3 server.py > loadbalancer.log 2>&1 &
        echo $! > loadbalancer.pid

        echo "All services started."
        ;;

    stop)
        echo "Stopping all services..."

        for file in server1.pid server2.pid server3.pid loadbalancer.pid
        do
            if [ -f "$file" ]; then
                kill "$(cat "$file")" 2>/dev/null
                rm -f "$file"
            fi
        done

        echo "All services stopped."
        ;;

    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;

    status)
        echo "Running processes:"
        pgrep -af "backend.py"
        pgrep -af "server.py"
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status}"
        ;;
esac
