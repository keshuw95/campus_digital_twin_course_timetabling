import numpy as np
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from math import radians, sin, cos, sqrt, atan2
import copy
import argparse


def haversine_distance(coord1, coord2):
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance in kilometers

def find_alternative_classrooms(c1_id, c2_id, input_data, topk=10, origin_location=None):
    """
    Find alternative classrooms and rank them using a combined metric based on normalized scores
    for distance_saved, time_saved, floors_saved, and occupancy_improved. 
    Handles negative values for occupancy_improved and includes support for origin as `c1_id`.
    """
    updated_courses_info, room_timetable, building_loc = input_data

    # Walking speed in m/s
    walking_speed_mps = 1.4

    # Check if c1_id is the origin
    if c1_id == "Origin" and origin_location:
        c1_info = {
            "course_number": "Origin",
            "room": "N/A",
            "building": "Origin Location",
            "building_id": "N/A",
            "building_location": origin_location,
            "start_time": "N/A",
            "end_time": "N/A",
            "floor": 1,
            "room_capacity": "N/A",
            "num_students": "N/A",
            "occupancy_rate": "N/A"
        }
        c1_location = origin_location
    else:
        # Fetch C1 details
        c1 = next(course for course in updated_courses_info['courses'] if course['CourseNumb'] == c1_id)
        c1_location = building_loc.get(str(int(c1['BuildingNumber'])))

        c1_info = {
            "course_number": c1['CourseNumb'],
            "room": c1['RoomNumber'],
            "building": c1['BuildingName'],
            "building_id": int(c1['BuildingNumber']),
            "building_location": (c1_location['lat'], c1_location['lon']),
            "start_time": c1['StartTimeStr'],
            "end_time": c1['EndTimeStr'],
            "floor": int(c1['RoomNumber'][0]) if c1['RoomNumber'][0].isdigit() else 1,
            "room_capacity": c1['RoomCapacity'],
            "num_students": c1['NumStudents'],
            "occupancy_rate": c1['NumStudents'] / c1['RoomCapacity'] if c1['RoomCapacity'] > 0 else 0
        }

    # Fetch C2 details
    c2 = next(course for course in updated_courses_info['courses'] if course['CourseNumb'] == c2_id)
    c2_location = building_loc.get(str(int(c2['BuildingNumber'])))

    c1_to_c2_distance = haversine_distance((c1_location['lat'], c1_location['lon']), (c2_location['lat'], c2_location['lon']))
    c1_to_c2_time = (c1_to_c2_distance * 1000) / walking_speed_mps / 60  # Convert to minutes
    c1_to_c2_floors = 0 if c1_id == "Origin" else abs(c1_info["floor"] - 1) + abs(int(c2['RoomNumber'][0]) if c2['RoomNumber'][0].isdigit() else 1 - 1)

    c2_info = {
        "course_number": c2['CourseNumb'],
        "room": c2['RoomNumber'],
        "building": c2['BuildingName'],
        "building_id": int(c2['BuildingNumber']),
        "building_location": (c2_location['lat'], c2_location['lon']),
        "start_time": c2['StartTimeStr'],
        "end_time": c2['EndTimeStr'],
        "floor": int(c2['RoomNumber'][0]) if c2['RoomNumber'][0].isdigit() else 1,
        "travel_distance": c1_to_c2_distance,
        "travel_time": c1_to_c2_time,
        "total_floors": c1_to_c2_floors,
        "room_capacity": c2['RoomCapacity'],
        "num_students": c2['NumStudents'],
        "occupancy_rate": c2['NumStudents'] / c2['RoomCapacity'] if c2['RoomCapacity'] > 0 else 0
    }

    # Available Classrooms During C2 Time
    start_time, end_time = c2['StartTimeStr'], c2['EndTimeStr']
    alternatives = []

    for building, rooms in room_timetable.items():
        for room, schedules in rooms.items():
            if all(not (schedule['StartTime'] < end_time and schedule['EndTime'] > start_time) for schedule in schedules):
                building_data = next((v for k, v in building_loc.items() if v['name'] == building), None)
                if building_data:
                    building_id = [k for k, v in building_loc.items() if v['name'] == building][0]
                    course_match = next((course for course in updated_courses_info['courses']
                                         if course['RoomNumber'] == room and course['BuildingName'] == building), None)
                    if not course_match or course_match['RoomCapacity'] < c2_info['num_students']:
                        continue  # Skip rooms that cannot accommodate the number of students

                    travel_distance = haversine_distance((c1_location['lat'], c1_location['lon']), (building_data['lat'], building_data['lon']))
                    travel_distance_m = travel_distance * 1000  # Convert to meters
                    travel_time = travel_distance_m / walking_speed_mps / 60  # Time in minutes
                    
                    # Calculate total floors traveled
                    alternative_floor = int(room[0]) if room[0].isdigit() else 1  # Default to 1st floor
                    total_floors = abs(c1_info["floor"] - 1) + abs(alternative_floor - 1)
                    
                    # Calculate savings compared to C2
                    distance_saved = c1_to_c2_distance - travel_distance
                    time_saved = c1_to_c2_time - travel_time
                    floors_saved = c1_to_c2_floors - total_floors
                    
                    # Add room capacity and calculate occupancy rate improvement
                    room_capacity = course_match['RoomCapacity']
                    num_students = c2_info['num_students']  # Use the number of students from C2
                    occupancy_rate = num_students / room_capacity if room_capacity > 0 else 0
                    occupancy_improved = occupancy_rate - c2_info['occupancy_rate']  # Improvement in occupancy rate

                    alternatives.append({
                        "course_number": c2['CourseNumb'],
                        "room": room,
                        "building": building,
                        "building_id": building_id,
                        "building_location": (building_data['lat'], building_data['lon']),
                        "start_time": c2['StartTimeStr'],
                        "end_time": c2['EndTimeStr'],
                        "travel_distance": travel_distance,
                        "travel_time": travel_time,
                        "total_floors": total_floors,
                        "room_capacity": room_capacity,
                        "num_students": num_students,
                        "distance_saved": distance_saved,
                        "time_saved": time_saved,
                        "floors_saved": floors_saved,
                        "occupancy_improved": occupancy_improved
                    })

    # Normalize and rank alternatives
    for metric in ["distance_saved", "time_saved", "floors_saved", "occupancy_improved"]:
        values = [alt[metric] for alt in alternatives]
        max_value = max(values)
        min_value = min(values)  # Handle negative values for occupancy_improved
        range_value = max_value - min_value if max_value != min_value else 1
        for alt in alternatives:
            alt[f"{metric}_normalized"] = (alt[metric] - min_value) / range_value  # Normalize to 0-1 range

    for alt in alternatives:
        alt["total_score"] = (
            alt["distance_saved_normalized"] +
            alt["time_saved_normalized"] +
            alt["floors_saved_normalized"] +
            alt["occupancy_improved_normalized"]
        )

    sorted_alternatives = sorted(alternatives, key=lambda x: x["total_score"], reverse=True)[:topk]

    return {
        "c1_info": c1_info,
        "c2_info": c2_info,
        "alternatives": sorted_alternatives,
    }


def reschedule(
    course_list,
    input_data,
    origin_lat_lon,
    origin_building_name,
    topk=3
):
    """
    Dynamically reschedule courses starting from the origin, updating the alternatives
    for each subsequent course based on the top-1 alternative selected for the previous course.
    """

    updated_courses_info, room_timetable, building_loc = input_data
    # Create a copy to dynamically record changes
    updated_courses_info_dynamic = copy.deepcopy(updated_courses_info)

    def update_course_info_dynamic(course_id, new_building, new_room, new_location, updated_courses_info_dynamic, building_loc):
        """
        Update the course information dynamically in updated_courses_info_dynamic.
        Ensure all necessary elements are updated, including building details, room details, and capacities.
        """
        building_number = None

        # Find the building number matching the new location
        for key, value in building_loc.items():
            if value["lat"] == new_location["lat"] and value["lon"] == new_location["lon"]:
                building_number = key
                break

        if building_number is None:
            raise ValueError(f"Building location {new_location} not found in building_loc")

        # Update the course information
        for course in updated_courses_info_dynamic['courses']:
            if course['CourseNumb'] == course_id:
                course['RoomNumber'] = new_room
                course['BuildingName'] = new_building
                course['BuildingNumber'] = building_number

                # Update related building attributes from `building_loc`
                building_data = building_loc[building_number]
                course['BldgAbbr'] = building_data.get("abbr", "N/A")  # Update building abbreviation
                course['Region'] = building_data.get("region", "N/A")  # Update region if available

                # Ensure capacity remains consistent
                course['RoomCapacity'] = building_data.get("room_capacity", course.get('RoomCapacity', "N/A"))

                # No change to other static attributes like `NumStudents`
                break

    course_chain = {}

    # Add origin to the chain
    origin_info = {
        "CourseNumb": "Origin",
        "room": "N/A",
        "building": origin_building_name,
        "building_location": origin_lat_lon,
        "start_time": "N/A",
        "end_time": "N/A",
        "floor": "N/A",
        "room_capacity": "N/A",
        "num_students": "N/A",
        "occupancy_rate": "N/A"
    }

    # Fetch options for the first course (C1) from Origin
    first_course_id = course_list[0]
    origin_result = find_alternative_classrooms(
        "Origin", first_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk, origin_location=origin_lat_lon
    )
    origin_options = origin_result["alternatives"]

    # Select the top-1 option for the first course (C1)
    top_option_c1 = origin_options[0] if origin_options else None

    # Add Origin information to the chain
    course_chain["Origin"] = {
        "id": 0,
        "original_current_course": origin_info,
        "original_next_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == first_course_id),
        "original_options_for_next_course": [
            {
                **opt,
                "metrics": {
                    "distance_saved": opt["distance_saved"],
                    "time_saved": opt["time_saved"],
                    "floors_saved": opt["floors_saved"],
                    "occupancy_improved": opt["occupancy_improved"],
                    "normalized": {
                        "distance_saved_normalized": opt["distance_saved_normalized"],
                        "time_saved_normalized": opt["time_saved_normalized"],
                        "floors_saved_normalized": opt["floors_saved_normalized"],
                        "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                    }
                },
                "total_score": opt["total_score"]
            } for opt in origin_options
        ],
        "updated_current_course": origin_info,
        "updated_options_for_next_course": [
            {
                **opt,
                "metrics": {
                    "distance_saved": opt["distance_saved"],
                    "time_saved": opt["time_saved"],
                    "floors_saved": opt["floors_saved"],
                    "occupancy_improved": opt["occupancy_improved"],
                    "normalized": {
                        "distance_saved_normalized": opt["distance_saved_normalized"],
                        "time_saved_normalized": opt["time_saved_normalized"],
                        "floors_saved_normalized": opt["floors_saved_normalized"],
                        "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                    }
                },
                "total_score": opt["total_score"]
            } for opt in origin_options
        ],
        "updated_next_course": top_option_c1
    }

    # Update C1 in updated_courses_info_dynamic based on the selected option
    if top_option_c1:
        update_course_info_dynamic(
            first_course_id,
            top_option_c1["building"],
            top_option_c1["room"],
            {"lat": top_option_c1["building_location"][0], "lon": top_option_c1["building_location"][1]},
            updated_courses_info_dynamic,
            building_loc
        )

    # Iterate over the rest of the course list
    for idx in range(len(course_list)):
        current_course_id = course_list[idx]
        if idx < len(course_list) - 1:
            next_course_id = course_list[idx + 1]

            # Fetch original options for the next course (C_{i+1}) based on updated current course (C_i)
            original_result = find_alternative_classrooms(
                current_course_id, next_course_id, (updated_courses_info, room_timetable, building_loc), topk
            )
            original_options = original_result["alternatives"]

            # Fetch updated options for the next course (C_{i+1}) based on updated current course (C_i)
            updated_result = find_alternative_classrooms(
                current_course_id, next_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk
            )
            updated_options = updated_result["alternatives"]

            # Select the top-1 option for the next course (C_{i+1})
            top_option_next = updated_options[0] if updated_options else None

            # Update the next course (C_{i+1}) in updated_courses_info_dynamic dynamically
            if top_option_next:
                update_course_info_dynamic(
                    next_course_id,
                    top_option_next["building"],
                    top_option_next["room"],
                    {"lat": top_option_next["building_location"][0], "lon": top_option_next["building_location"][1]},
                    updated_courses_info_dynamic,
                    building_loc
                )

            # Add information for the current course to the chain
            course_chain[f"Course_{idx + 1}"] = {
                "id": idx + 1,
                "original_current_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == current_course_id),
                "original_next_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == next_course_id),
                "original_options_for_next_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in original_options
                ],
                "updated_current_course": next(course for course in updated_courses_info_dynamic["courses"] if course["CourseNumb"] == current_course_id),
                "updated_options_for_next_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in updated_options
                ],
                "updated_next_course": top_option_next
            }
        else:
            # For the last course, add its information without "next course" details
            last_result = find_alternative_classrooms(
                current_course_id, current_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk
            )
            last_options = last_result["alternatives"]

            course_chain[f"Course_{idx + 1}"] = {
                "id": idx + 1,
                "original_current_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == current_course_id),
                "original_options_for_current_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in last_options
                ],
                "updated_current_course": next(course for course in updated_courses_info_dynamic["courses"] if course["CourseNumb"] == current_course_id)
            }

    return course_chain


def radar_charts(course_chain, subplots_per_row=5):
    """
    Plot radar charts for the four metrics (distance_saved, time_saved, floors_saved, occupancy_improved)
    for all the options of each course in the course chain, with adjustable subplots per row and enhanced visuals.
    """

    # Metrics and their normalized counterparts
    metrics = ["distance_saved", "time_saved", "floors_saved", "occupancy_improved"]
    normalized_metrics = [f"{metric}_normalized" for metric in metrics]
    num_metrics = len(normalized_metrics)
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Close the radar chart loop

    # Define nicer labels for the metrics
    metric_labels = {
        "distance_saved_normalized": "Distance\nSaved",
        "time_saved_normalized": "Time\nSaved",
        "floors_saved_normalized": "Floors\nSaved",
        "occupancy_improved_normalized": "Occupancy\nImproved"
    }

    # Define colors for better visual effect
    color_palette = list(mcolors.TABLEAU_COLORS.values())

    # Loop through each course in the chain, sorted by ID for consistency
    for course_key in sorted(course_chain.keys(), key=lambda k: course_chain[k]["id"]):
        course_data = course_chain[course_key]
        # print(course_data)
        # Ensure there are options available for radar plotting
        if "updated_options_for_next_course" not in course_data or not course_data["updated_options_for_next_course"]:
            continue

        options = course_data["updated_options_for_next_course"]
        num_options = len(options)
        rows = (num_options + subplots_per_row - 1) // subplots_per_row
        fig, axs = plt.subplots(rows, subplots_per_row, figsize=(subplots_per_row * 3, rows * 3), subplot_kw=dict(polar=True))
        axs = axs.flatten() if num_options > 1 else [axs]

        # Retrieve the course ID for the title
        current_course_id = course_data["updated_next_course"]["course_number"]
        start_time = course_data["original_next_course"]["StartTimeStr"]
        end_time = course_data["original_next_course"]["EndTimeStr"]
        for i, option in enumerate(options):
            values = [option["metrics"]["normalized"].get(metric, 0) for metric in normalized_metrics]
            values += values[:1]  # Close the radar chart loop
            ax = axs[i]
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)

            # Plot the radar chart for this option
            ax.plot(angles, values, label=f"Room: {option['room']}", color=color_palette[i % len(color_palette)])
            ax.fill(angles, values, alpha=0.25, color=color_palette[i % len(color_palette)])

            # Add gridlines and labels
            ax.set_yticks([0.25, 0.5, 0.75, 1])
            ax.set_yticklabels(["0.25", "0.5", "0.75", "1"], fontsize=10)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels([metric_labels[m] for m in normalized_metrics], fontsize=10)
            total_score = option.get("total_score", 0)
            ax.set_title(
                f"{option['building']}\nRoom: $\mathbf{{{option['room']}}}$\nTotal Score: $\mathbf{{{total_score:.2f}}}$",
                va="bottom",
                fontsize=10
            )

        # Add empty subplots if necessary
        for j in range(num_options, len(axs)):
            fig.delaxes(axs[j])  # Mark unused axes as empty


        # Correctly set suptitle from the first course to the last
        suptitle = f"Options of Course ID: $\mathbf{{{current_course_id}}}$\n{start_time} - {end_time}"
        fig.suptitle(suptitle, fontsize=14)
        plt.tight_layout()
        plt.show()


def dynamic_reschedule(
    course_list,
    data,
    origin_lat_lon,
    origin_building_name,
    selection_indices, 
    topk=3
):
    """
    Dynamically reschedule courses starting from the origin, using manual input for selection
    from the alternatives for each course in the list.
    """
    updated_courses_info, room_timetable, building_loc = data

    # Create a copy to dynamically record changes
    updated_courses_info_dynamic = copy.deepcopy(updated_courses_info)

    def update_course_info_dynamic(course_id, new_building, new_room, new_location, updated_courses_info_dynamic, building_loc):
        """
        Update the course information dynamically in updated_courses_info_dynamic.
        Ensure all necessary elements are updated, including building details, room details, and capacities.
        """
        building_number = None

        # Find the building number matching the new location
        for key, value in building_loc.items():
            if value["lat"] == new_location["lat"] and value["lon"] == new_location["lon"]:
                building_number = key
                break

        if building_number is None:
            raise ValueError(f"Building location {new_location} not found in building_loc")

        # Update the course information
        for course in updated_courses_info_dynamic['courses']:
            if course['CourseNumb'] == course_id:
                course['RoomNumber'] = new_room
                course['BuildingName'] = new_building
                course['BuildingNumber'] = building_number

                # Update related building attributes from `building_loc`
                building_data = building_loc[building_number]
                course['BldgAbbr'] = building_data.get("abbr", "N/A")  # Update building abbreviation
                course['Region'] = building_data.get("region", "N/A")  # Update region if available

                # Ensure capacity remains consistent
                course['RoomCapacity'] = building_data.get("room_capacity", course.get('RoomCapacity', "N/A"))

                # No change to other static attributes like `NumStudents`
                break

    course_chain = {}

    # Add origin to the chain
    origin_info = {
        "CourseNumb": "Origin",
        "room": "N/A",
        "building": origin_building_name,
        "building_location": origin_lat_lon,
        "start_time": "N/A",
        "end_time": "N/A",
        "floor": "N/A",
        "room_capacity": "N/A",
        "num_students": "N/A",
        "occupancy_rate": "N/A"
    }

    # Fetch options for the first course (C1) from Origin
    first_course_id = course_list[0]
    origin_result = find_alternative_classrooms(
        "Origin", first_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk, origin_location=origin_lat_lon
    )
    origin_options = origin_result["alternatives"]

    # Select manually the option for the first course (C1)
    selected_index_c1 = selection_indices[0]
    selected_option_c1 = origin_options[selected_index_c1] if origin_options and selected_index_c1 < len(origin_options) else None

    # Add Origin information to the chain
    course_chain["Origin"] = {
        "id": 0,
        "original_current_course": origin_info,
        "original_next_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == first_course_id),
        "original_options_for_next_course": [
            {
                **opt,
                "metrics": {
                    "distance_saved": opt["distance_saved"],
                    "time_saved": opt["time_saved"],
                    "floors_saved": opt["floors_saved"],
                    "occupancy_improved": opt["occupancy_improved"],
                    "normalized": {
                        "distance_saved_normalized": opt["distance_saved_normalized"],
                        "time_saved_normalized": opt["time_saved_normalized"],
                        "floors_saved_normalized": opt["floors_saved_normalized"],
                        "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                    }
                },
                "total_score": opt["total_score"]
            } for opt in origin_options
        ],
        "updated_current_course": origin_info,
        "updated_options_for_next_course": [
            {
                **opt,
                "metrics": {
                    "distance_saved": opt["distance_saved"],
                    "time_saved": opt["time_saved"],
                    "floors_saved": opt["floors_saved"],
                    "occupancy_improved": opt["occupancy_improved"],
                    "normalized": {
                        "distance_saved_normalized": opt["distance_saved_normalized"],
                        "time_saved_normalized": opt["time_saved_normalized"],
                        "floors_saved_normalized": opt["floors_saved_normalized"],
                        "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                    }
                },
                "total_score": opt["total_score"]
            } for opt in origin_options
        ],
        "updated_next_course": selected_option_c1
    }

    # Update C1 in updated_courses_info_dynamic based on the selected option
    if selected_option_c1:
        update_course_info_dynamic(
            first_course_id,
            selected_option_c1["building"],
            selected_option_c1["room"],
            {"lat": selected_option_c1["building_location"][0], "lon": selected_option_c1["building_location"][1]},
            updated_courses_info_dynamic,
            building_loc
        )

    # Iterate over the rest of the course list
    for idx in range(len(course_list)):
        current_course_id = course_list[idx]
        if idx < len(course_list) - 1:
            next_course_id = course_list[idx + 1]

            # Fetch original options for the next course (C_{i+1}) based on updated current course (C_i)
            original_result = find_alternative_classrooms(
                current_course_id, next_course_id, (updated_courses_info, room_timetable, building_loc), topk
            )
            original_options = original_result["alternatives"]

            # Fetch updated options for the next course (C_{i+1}) based on updated current course (C_i)
            updated_result = find_alternative_classrooms(
                current_course_id, next_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk
            )
            updated_options = updated_result["alternatives"]

            # Select manually the option for the next course (C_{i+1})
            selected_index_next = selection_indices[idx + 1]
            selected_option_next = updated_options[selected_index_next] if updated_options and selected_index_next < len(updated_options) else None

            # Update the next course (C_{i+1}) in updated_courses_info_dynamic dynamically
            if selected_option_next:
                update_course_info_dynamic(
                    next_course_id,
                    selected_option_next["building"],
                    selected_option_next["room"],
                    {"lat": selected_option_next["building_location"][0], "lon": selected_option_next["building_location"][1]},
                    updated_courses_info_dynamic,
                    building_loc
                )

            # Add information for the current course to the chain
            course_chain[f"Course_{idx + 1}"] = {
                "id": idx + 1,
                "original_current_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == current_course_id),
                "original_next_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == next_course_id),
                "original_options_for_next_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in original_options
                ],
                "updated_current_course": next(course for course in updated_courses_info_dynamic["courses"] if course["CourseNumb"] == current_course_id),
                "updated_options_for_next_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in updated_options
                ],
                "updated_next_course": selected_option_next
            }
        else:
            # For the last course, add its information without "next course" details
            last_result = find_alternative_classrooms(
                current_course_id, current_course_id, (updated_courses_info_dynamic, room_timetable, building_loc), topk
            )
            last_options = last_result["alternatives"]

            course_chain[f"Course_{idx + 1}"] = {
                "id": idx + 1,
                "original_current_course": next(course for course in updated_courses_info["courses"] if course["CourseNumb"] == current_course_id),
                "original_options_for_current_course": [
                    {
                        **opt,
                        "metrics": {
                            "distance_saved": opt["distance_saved"],
                            "time_saved": opt["time_saved"],
                            "floors_saved": opt["floors_saved"],
                            "occupancy_improved": opt["occupancy_improved"],
                            "normalized": {
                                "distance_saved_normalized": opt["distance_saved_normalized"],
                                "time_saved_normalized": opt["time_saved_normalized"],
                                "floors_saved_normalized": opt["floors_saved_normalized"],
                                "occupancy_improved_normalized": opt["occupancy_improved_normalized"]
                            }
                        },
                        "total_score": opt["total_score"]
                    } for opt in last_options
                ],
                "updated_current_course": next(course for course in updated_courses_info_dynamic["courses"] if course["CourseNumb"] == current_course_id)
            }

    return course_chain


def main(course_list, origin_lat_lon, origin_building_name, selection_indices, topk=10):
    """
    Main function for dynamic classroom rescheduling.
    Args:
        course_list: List of course IDs.
        origin_lat_lon: Dictionary with latitude and longitude of the origin.
        origin_building_name: Name of the origin building.
        selection_indices: List of indices for manual selection.
        topk: Number of top alternatives to consider.
    Returns:
        JSON-like dictionary containing the reschedule chain.
    """

    with open('./data/courses_info.json', 'r') as f:
        courses_info = json.load(f)
    with open('./data/building_loc.json', 'r') as f:
        building_loc = json.load(f)
    with open('./data/room_timetable.json', 'r') as f:
        room_timetable = json.load(f)

    input_data = (courses_info, room_timetable, building_loc)

    dynamic_course_chain = dynamic_reschedule(
        course_list,
        input_data,
        origin_lat_lon,
        origin_building_name,
        selection_indices,
        topk=topk
    )

    return dynamic_course_chain

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dynamically reschedule classrooms.")
    parser.add_argument("--course_list", nargs="+", type=int, default=[325, 661, 301, 612, 321], help="List of course IDs.")
    parser.add_argument("--origin_lat", type=float, default=30.61507082693666, help="Latitude of the origin.")
    parser.add_argument("--origin_lon", type=float, default=-96.34047976538754, help="Longitude of the origin.")
    parser.add_argument("--origin_building_name", type=str, default="Nagle Hall", help="Name of the origin building.")
    parser.add_argument("--selection_indices", nargs="+", type=int, default=[0, 0, 0, 0, 0], help="Indices for manual selection.")
    parser.add_argument("--topk", type=int, default=10, help="Number of top alternatives to consider.")
    args = parser.parse_args()

    course_chain = main(
        args.course_list,
        {"lat": args.origin_lat, "lon": args.origin_lon},
        args.origin_building_name,
        args.selection_indices,
        args.topk
    )
    # output = json.dumps(course_chain, indent=4)
    
    # print(output)
    # radar_charts(course_chain)

    with open("./data/output.json", "w") as f:
        output = json.dump(course_chain, f, indent=4)
    