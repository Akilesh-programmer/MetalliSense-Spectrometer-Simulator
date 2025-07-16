import random
from datetime import datetime
from db import get_metal_grade_spec

def inject_noise(value, noise_level=0.005):
    return round(value + random.uniform(-noise_level, noise_level), 4)

def inject_anomaly(value, chance=0.05, spike_factor=2.0, max_limit=1.0):
    if random.random() < chance:
        return min(round(value * spike_factor, 4), max_limit)
    return value

def generate_within_range(min_val, max_val):
    value = random.uniform(min_val, max_val)
    return round(inject_noise(value), 4)

def generate_out_of_range(min_val, max_val, deviation=0.15):
    direction = random.choice(['low', 'high'])
    if direction == 'low':
        value = random.uniform(min_val - deviation, min_val - 0.01)
    else:
        value = random.uniform(max_val + 0.01, max_val + deviation)
    return round(inject_noise(value), 4)

def simulate_reading(grade="SG-Iron", incorrect_elements_count=3):
    profile = get_metal_grade_spec(grade)
    all_elements = list(profile.keys())
    incorrect_elements = random.sample(all_elements, k=incorrect_elements_count)
    
    reading = {}

    for element, limits in profile.items():
        min_val, max_val = limits
        if element in incorrect_elements:
            value = generate_out_of_range(min_val, max_val)
            if element in ['S', 'P', 'Pb', 'Mn']:
                value = inject_anomaly(value)
        else:
            value = generate_within_range(min_val, max_val)

        reading[element] = round(value, 4)

    reading["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return reading
