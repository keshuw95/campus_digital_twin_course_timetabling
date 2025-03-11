# Course Timetabling Optimization 📊


## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Usage](#usage)
   - [Example](#example)
   - [Arguments](#arguments)
4. [Output](#output)
   - [Output JSON Structure](#output-json-structure)
   - [Key Metrics](#key-metrics)
   - [Normalization](#normalization)
   - [Total Score](#total-score)
   - [Using `selection_indices`](#using-selection_indices)
5. [Notebooks](#notebooks)
   - [Introduction to `radarmap_alternatives.ipynb`](#introduction-to-radarmap_alternativesipynb)
   - [Introduction to `timetable_map_viz.ipynb`](#introduction-to-timetable_map_vizipynb)
   - [Introduction to `optimization_metrics.ipynb`](#introduction-to-optimization_metricsipynb)


--- 

## Overview
This repository contains the Python implementation for dynamic course timetabling optimization. The program identifies the optimal schedule by analyzing travel distances, room capacities, occupancy rates, and other constraints.

## Features
- Supports manual selection of classroom alternatives for courses.
- Computes and normalizes metrics such as distance saved, time saved, floors saved, and occupancy improvement.
- Provides a JSON output detailing the optimal course schedule and its alternatives.

---

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
- `--course_list`: List of course IDs in the sequence.
- `--origin_lat_lon`: Latitude and longitude of the origin.
- `--origin_building_name`: Name of the origin building.
- `--selection_indices`: List of indices for manually selecting room alternatives.
- `--topk`: Number of top room alternatives to consider for each course.

## Output
The program generates a JSON file containing detailed scheduling information, including metrics and normalized scores for each alternative.

## Output JSON Structure
The output JSON contains scheduling details for the origin and each course. Below is the structure:

### Keys Explanation
- `original_current_course`: The original course details before optimization for the current course.
- `original_next_course`: The original course details before optimization for the next course.
- `original_options_for_next_course`: A list of all possible room alternatives for the next course, including metrics and normalized scores.
- `updated_current_course`: The updated course details after optimization for the current course.
- `updated_options_for_next_course`: A list of all possible room alternatives for the next course based on the optimized current course location.
- `updated_next_course`: The selected optimized room and location for the next course.

### Origin
```bash
"Origin": {
    "id": 0,
    "original_current_course": {
        "CourseNumb": "Origin",
        "room": "N/A",
        "building": "Nagle Hall",
        "building_location": {
            "lat": <latitude>,
            "lon": <longitude>
        },
        ...
    },
    ...
```

### Course_N
```bash
"Course_N": {
    "id": <integer>,
    "original_current_course": {
        "CourseNumb": <course_number>,
        ...
    },
    "original_next_course": {
        "CourseNumb": <course_number>,
        ...
    },
    "original_options_for_next_course": [
        {
            "course_number": <course_number>,
            "room": <room_number>,
            ...
            "metrics": {
                "distance_saved": <value>,
                ...
                "normalized": {
                    "distance_saved_normalized": <value>,
                    ...
                }
            }
        },
        ...
    ],
    "updated_current_course": {
        "CourseNumb": <course_number>,
        ...
    },
    "updated_options_for_next_course": [
        {
            "course_number": <course_number>,
            "room": <room_number>,
            ...
            "metrics": {
                "distance_saved": <value>,
                ...
                "normalized": {
                    "distance_saved_normalized": <value>,
                    ...
                }
            }
        },
        ...
    ],
    "updated_next_course": {
        "course_number": <course_number>,
        "room": <room_number>,
        ...
    }
}
```

---

## Key Metrics
Each alternative includes:
- `distance_saved`: Distance saved (in km).
- `time_saved`: Time saved (in minutes).
- `floors_saved`: Number of floors saved.
- `occupancy_improved`: Improvement in room occupancy rate.

### Normalization
- Normalized metrics scale values between 0 and 1.
- `distance_saved_normalized`, `time_saved_normalized`, `floors_saved_normalized`, `occupancy_improved_normalized`.

### Total Score
- The `total_score` is a composite score calculated by summing the normalized metrics:
```bash
total_score = distance_saved_normalized 
              + time_saved_normalized 
              + floors_saved_normalized 
              + occupancy_improved_normalized
```
- This score represents the overall suitability of an alternative, with higher scores indicating better options.
- Alternatives are ranked based on the `total_score`.

### Using `selection_indices`
- The selection_indices argument specifies which alternative to select for each course.
- For example:
- ```bash
  selection_indices = [1, 4, 6, 4, 1]
  ```
  indicates:
    - Use the 2nd alternative (`index = 1`) for the first course.
    - Use the 5th alternative (`index = 4`) for the second course, and so on.
- The program dynamically updates the schedule based on the chosen alternatives from `selection_indices`.
- If an index is out of bounds or no valid option is available, the program skips that course or uses a default fallback.

---

## Introduction to `radarmap_alternatives.ipynb`

### Overview
This Jupyter Notebook optimizes classroom assignments in course timetabling by analyzing travel distances, walking times, floor changes, and occupancy efficiency.

### Core Steps

1. **Load Data**
   - Import course schedules, building locations, and room timetables.

2. **Identify Alternative Classrooms**
   - Retrieve available rooms with sufficient capacity.
   - Compute travel distance, walking time, and floor changes.

3. **Compute and Normalize Metrics**
   - Key metrics: `distance_saved`, `time_saved`, `floors_saved`, and `occupancy_improved`.
   - Normalize values (0 to 1) and rank alternatives.

4. **Rank and Select Alternatives**
   - Compute a `total_score` by summing normalized values.
   - Select the top-k classroom alternatives.

5. **Dynamic Rescheduling**
   - Adjust course assignments iteratively using `selection_indices`.

6. **Generate JSON Output**
   - Store original vs. updated assignments, rankings, and schedule details.

7. **Visualization**
   - Use radar charts to compare trade-offs in alternative classrooms.

### Usage in Course Timetabling Optimization
This notebook enhances scheduling efficiency by minimizing student travel time and improving classroom utilization.

---
## Introduction to `timetable_map_viz.ipynb`

### Overview
This notebook visualizes student transitions, travel times, and classroom utilization to support course timetabling decisions.

### Core Steps

1. **Load Data**
   - Import course schedules, student enrollments, and building locations.

2. **Analyze Student Transitions**
   - Identify consecutive courses within a 20-minute window.
   - Construct and visualize a course transition network.

3. **Compute Travel Distances & Times**
   - Use the Haversine formula for building-to-building distances.
   - Estimate travel times for walking, biking, and bus transportation.

4. **Visualize Student Movement Impact**
   - Heatmaps for travel distances, time spent commuting, and total student movement.

5. **Generate Optimal Route Maps**
   - Identify frequent transitions and plot optimal walking routes.

6. **Classroom Usage & Campus Mapping**
   - Visualize classroom occupancy and building locations on campus maps.

### Usage in Course Timetabling Optimization
This notebook provides spatial insights to optimize schedules, minimize congestion, and improve student mobility.


---

## Introduction to `optimization_metrics.ipynb`

### Overview
This Jupyter Notebook evaluates and optimizes classroom assignments by analyzing travel distances, travel times, floor changes, and occupancy rates. It implements an iterative optimization process to minimize student movement inefficiencies.

### Core Steps

1. **Load Data**
   - Import JSON files containing course schedules, building locations, and room timetables.

2. **Compute Travel Metrics**
   - Identify course transitions with a gap of ≤ 20 minutes.
   - Compute:
     - `travel_distance`: Distance between consecutive course buildings.
     - `travel_time`: Estimated walking time.
     - `floors_traveled`: Number of floors changed.
     - `occupancy_rate`: Room occupancy efficiency.

3. **Bottleneck Identification**
   - Determine the highest-impact course transitions based on student movement and travel burden.

4. **Find Alternative Classrooms**
   - Search for available classrooms that reduce travel burden.
   - Prioritize alternatives that minimize distance, time, and floor transitions while maintaining capacity.

5. **Iterative Optimization**
   - Reassign classrooms iteratively to reduce travel inefficiencies.
   - Update room schedules dynamically to reflect changes.

6. **Visualization of Optimization Results**
   - Plot histograms comparing pre- and post-optimization distributions for:
     - Travel distance
     - Travel time
     - Floors traveled
     - Occupancy rates

7. **Classroom Timetable Visualization**
   - Generate before-and-after heatmaps showing classroom occupancy.
   - Highlight reallocated courses and room assignments.

### Usage in Course Timetabling Optimization
This notebook supports the `Course Timetabling Optimization` framework by optimizing classroom assignments, minimizing student travel time, and improving overall scheduling efficiency.
