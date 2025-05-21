#!/bin/bash
uvicorn pets.main:app --host 0.0.0.0 --port 10000
