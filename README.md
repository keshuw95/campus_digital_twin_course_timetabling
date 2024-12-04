# Course Timetabling Optimization README

## Overview
This repository contains the Python implementation for dynamic course timetabling optimization. The program identifies the optimal schedule by analyzing travel distances, room capacities, occupancy rates, and other constraints.

## Features
- Supports manual selection of classroom alternatives for courses.
- Computes and normalizes metrics such as distance saved, time saved, floors saved, and occupancy improvement.
- Provides a JSON output detailing the optimal course schedule and its alternatives.

## Usage
Run the program using the command line with the following syntax:
```bash
python course_timetabling.py --course_list [list_of_courses] \
    --origin_lat_lon [latitude longitude] \
    --origin_building_name [building_name] \
    --selection_indices [list_of_indices] \
    --topk [number_of_alternatives]

