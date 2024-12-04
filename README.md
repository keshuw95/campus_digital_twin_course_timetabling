# Course Timetabling Optimization

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
