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
```
## Example
```bash
python course_timetabling.py --course_list 325 661 463 612 321 \
    --origin_lat_lon 30.61507082693666 -96.34047976538754 \
    --origin_building_name "Nagle Hall" \
    --selection_indices 1 4 6 4 1 \
    --topk 10
```
## Arguments
- --course_list: List of course IDs in the sequence.
- --origin_lat_lon: Latitude and longitude of the origin.
- --origin_building_name: Name of the origin building.
- --selection_indices: List of indices for manually selecting room alternatives.
- --topk: Number of top room alternatives to consider for each course.
