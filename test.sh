#!/bin/bash
# Test runner convenience script for radio-streamer

case "$1" in
    "fast")
        python run_tests.py --fast
        ;;
    "unit")
        python run_tests.py --unit
        ;;
    "integration") 
        python run_tests.py --integration
        ;;
    "api")
        python run_tests.py --api
        ;;
    "coverage")
        python run_tests.py --coverage
        ;;
    "install")
        python run_tests.py --install-deps
        ;;
    *)
        python run_tests.py --all
        ;;
esac
