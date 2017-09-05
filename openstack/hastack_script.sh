#!/bin/bash
###############################################################
## Update : yuanpeng
## Update Date : 2016/11/15
## Running by root, Install on keepalived server
## Function : keepalived script of checking novip services
## For All of Linux
###############################################################

proc_name=$1
anti_zombie=$2
time=`date`
log_path="/var/log/keepalived/check_${proc_name}.log"
state_path="/var/run/${proc_name}_state"
interval=5

check_exist=`ps -C "$proc_name" --no-header`
state=`cat $state_path`
case $state in
    "MASTER")
        if [ "$check_exist" == "" ]; then
            service $proc_name start
            sleep $interval
            check_exist=`ps -C "$proc_name" --no-header`
            if [ "$check_exist" != "" ]; then
                echo "[$time] [$state] $proc_name down, but rise up again, return 0" >> $log_path
                exit 0
            fi
            echo "[$time] [$state] $proc_name can not rise up, return 1" >> $log_path
            exit 1
        else
            if [ -f "$anti_zombie" ]; then
                rm -f $anti_zombie
                echo "[$time] [$state] $proc_name is running, return 0" >> $log_path
            else
                echo "[$time] [$state] $proc_name turned into zombie, trying restart..." >> $log_path
                service $proc_name restart
                sleep $interval
                if [ ! -f "$anti_zombie" ]; then
                    echo "[$time] [$state] $proc_name can't be rescued, damn!" >> $log_path
                    exit 1
                fi
            fi
            exit 0
        fi
        ;;
    "BACKUP")
        if [ "$check_exist" == "" ]; then
            echo "[$time] [$state] $proc_name is not running" >> $log_path
        else
            echo "[$time] [$state] $proc_name is running at backup node, kill it" >> $log_path
            service $proc_name stop
            pkill -9 $proc_name
        fi
        exit 0
        ;;
    "ABNORMAL")
        echo "[$time] [$state] $proc_name is abnormal, return 1" >> $log_path
        exit 1
        ;;
    "FAULT")
        echo "[$time] [$state] $proc_name state is fault, restart keepalived, return 1" >> $log_path
        case $proc_name in
            "hastack-service")
                service keepalived_vmha restart
                ;;
            *)
                ;;
        esac
        exit 1
        ;;
    *)
        exit 0
        ;;
esac
