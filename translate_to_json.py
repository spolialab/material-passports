import csv
import json
from datetime import datetime

def convert_carbon_locations_to_json(csv_file):
    reconfigurations = []
    
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            # Skip empty rows
            if not row['Reconfiguration number']:
                continue
                
            # Parse coordinates
            coords = row['Location coordinates'].replace('° N', '').replace('° W', '').replace('° E', '').split(',')
            lat = float(coords[0]) if coords[0].strip() else None
            # Convert West longitude to negative
            lon = float(coords[1]) if coords[1].strip() else None
            if 'W' in row['Location coordinates']:
                lon = -lon if lon else None
            
            # Parse date - use the Date (approx) field directly
            date = row['Date (approx) '].strip() if row['Date (approx) '] else None
            
            reconfiguration = {
                "number": int(row['Reconfiguration number']),
                "name": row['Reconfiguration name'],
                "date": date,  # Add the date here
                "location": {
                    "name": row['Location name'],
                    "coordinates": {
                        "latitude": lat,
                        "longitude": lon
                    }
                },
                "pixel_weight": float(row['Pixel weight (kg)']) if row['Pixel weight (kg)'] else None,
                "coefficient": float(row['Coefficient']) if row['Coefficient'] else None,
                "a1_a3_emissions": float(row['A1-A3 emissions (kgCO2e)']) if row['A1-A3 emissions (kgCO2e)'] else None,
                "transport": {
                    "distance": float(row['Transport distance (km)']) if row['Transport distance (km)'] else 0,
                    "type": row['Type of transport'],
                    "coefficient": float(row['Transport coefficient (kgCO2e/kg)']) if row['Transport coefficient (kgCO2e/kg)'] else None,
                    "emissions": float(row['Carbon emissions (A4) (kgCO2e/pixel)']) if row['Carbon emissions (A4) (kgCO2e/pixel)'] else 0
                },
                "total_emissions": float(row['Total emissions per reconfiguration (kgCO2e/pixel)']) if row['Total emissions per reconfiguration (kgCO2e/pixel)'] else None
            }
            reconfigurations.append(reconfiguration)
    
    return {"reconfigurations": reconfigurations}

def convert_master_to_json(csv_file):
    pixels = []
    
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            # Skip empty rows
            if not row['Pixel number']:
                continue
                
            # Create reconfigurations dictionary
            reconfigurations = {}
            reconfig_names = {
                1: "Reconfiguration 1 (Gen 1 Load Test Beam) - Cambridge MA",
                2: "Reconfiguration 2 (Gen 1 Prototype Column) - Cambridge MA",
                3: "Reconfiguration 3 (Gen 1 Shear Test)",
                4: "Reconfiguration 4 (Gen 2 Showcase Beam) - Washington DC",
                5: "Reconfiguration 5 (Gen 2 Showcase Column) - Washington DC",
                6: "Reconfiguration 6 (Gen 1 Showcase Column) - Cambridge MA",
                7: "Reconfiguration 7 (Gen 2 Thesis Beam) - Cambridge MA",
                8: "Reconfiguration 8 (Gen 1 Thesis Column) - Cambridge MA",
                9: "Reconfiguration 9 (Biennale Beam)",
                10: "Reconfiguration 10 (Biennale Column) ",
                11: "Reconfiguration 11 (Speculative Reconfiguration - Warehouse)",
                12: "Reconfiguration 12 (Speculative Reconfiguration - Warehouse)",
                13: "Reconfiguration 13 (Speculative Reconfiguration - Tower)"
            }
            
            for i in range(1, 14):
                column_name = reconfig_names[i]
                reconfigurations[str(i)] = bool(int(row[column_name])) if row[column_name].strip() == '1' else False
            
            pixel = {
                "pixel_number": int(row['Pixel number']),
                "generation": int(row['Generation']) if row['Generation'] else None,
                "fc": float(row["fc'"]) if row["fc'"] else None,
                "weight": float(row['Weight (kg)']) if row['Weight (kg)'] else None,
                "carbon_emissions_a1_a3": float(row['Carbon emissions (A1-A3)']) if row['Carbon emissions (A1-A3)'] else None,
                "concrete_mix": row['Concrete mix'].strip() if row['Concrete mix'] else None,
                "fiber": {
                    "type": row['Fiber type'].strip() if row['Fiber type'] else None,
                    "dosage": row['Fiber dosage'].strip() if row['Fiber dosage'] else None
                },
                "date_of_manufacture": row['Date of manufacture'],
                "number_of_reconfigurations": int(row['Number of reconfigurations']) if row['Number of reconfigurations'] else None,
                "condition": row['Condition'] if row['Condition'] else None,
                "reconfigurations": reconfigurations,
                "gif": row['GIF'].lower() == 'yes' if row['GIF'] else False,
                "notes": row['notes'] if row['notes'] else None
            }
            pixels.append(pixel)
    
    return {"pixels": pixels}

def create_timeline_json(master_csv, carbon_locations_csv):
    # First, load and parse both CSV files into dictionaries for easier lookup
    carbon_data = {}
    with open(carbon_locations_csv, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            carbon_data[int(row['Reconfiguration number'])] = {
                'name': row['Reconfiguration name'],
                'date': row['Date (approx) '],
                'location': {
                    'name': row['Location name'],
                    'coordinates': {
                        'latitude': float(row['Location coordinates'].split('° N')[0].strip()),
                        'longitude': float(row['Location coordinates'].split(',')[1].replace('° W', '').replace('° E', '').strip()) * (-1 if '° W' in row['Location coordinates'] else 1)
                    }
                },
                'transport': {
                    'type': row['Type of transport'],
                    'distance': float(row['Transport distance (km)']) if row['Transport distance (km)'] else 0,
                    'emissions': float(row['Carbon emissions (A4) (kgCO2e/pixel)']) if row['Carbon emissions (A4) (kgCO2e/pixel)'] else 0
                },
                'a1_a3_emissions': float(row['A1-A3 emissions (kgCO2e)']) if row['A1-A3 emissions (kgCO2e)'] else 0
            }

    # Process each pixel's timeline
    pixels_timeline = []
    with open(master_csv, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if not row['Pixel number']:
                continue

            pixel_number = int(row['Pixel number'])
            reconfig_columns = {
                i: f"Reconfiguration {i}" + (
                    " (Gen 1 Load Test Beam) - Cambridge MA" if i == 1 else
                    " (Gen 1 Prototype Column) - Cambridge MA" if i == 2 else
                    " (Gen 1 Shear Test)" if i == 3 else
                    " (Gen 2 Showcase Beam) - Washington DC" if i == 4 else
                    " (Gen 2 Showcase Column) - Washington DC" if i == 5 else
                    " (Gen 1 Showcase Column) - Cambridge MA" if i == 6 else
                    " (Gen 2 Thesis Beam) - Cambridge MA" if i == 7 else
                    " (Gen 1 Thesis Column) - Cambridge MA" if i == 8 else
                    " (Biennale Beam)" if i == 9 else
                    " (Biennale Column) " if i == 10 else
                    " (Speculative Reconfiguration - Warehouse)" if i == 11 else
                    " (Speculative Reconfiguration - Warehouse)" if i == 12 else
                    " (Speculative Reconfiguration - Tower)"
                ) for i in range(1, 14)
            }

            # Get chronological list of reconfigurations for this pixel
            reconfigurations = []
            for i in range(1, 14):
                if row[reconfig_columns[i]].strip() == '1':
                    reconfigurations.append(i)

            if not reconfigurations:
                continue

            # Build timeline for this pixel
            timeline = []
            cumulative_emissions = 0
            cumulative_distance = 0
            
            for step, reconfig_num in enumerate(reconfigurations, 1):
                reconfig_data = carbon_data[reconfig_num]
                
                # Calculate emissions and distance for this step
                a1_a3 = reconfig_data['a1_a3_emissions'] if step == 1 else 0
                transport_emissions = reconfig_data['transport']['emissions']
                step_distance = reconfig_data['transport']['distance']
                
                # Update cumulative totals
                cumulative_emissions += (a1_a3 + transport_emissions)
                cumulative_distance += step_distance

                timeline_entry = {
                    "step": step,
                    "reconfiguration_number": reconfig_num,
                    "date": reconfig_data['date'],
                    "location": reconfig_data['location'],
                    "emissions": {
                        "a1_a3": a1_a3,
                        "transport": transport_emissions,
                        "step_total": a1_a3 + transport_emissions,
                        "running_total": cumulative_emissions
                    },
                    "transport": {
                        "type": reconfig_data['transport']['type'],
                        "distance": step_distance,
                        "cumulative_distance": cumulative_distance
                    }
                }
                timeline.append(timeline_entry)

            pixel_timeline = {
                "pixel_number": pixel_number,
                "timeline": timeline,
                "total_emissions": cumulative_emissions,
                "total_distance": cumulative_distance
            }
            pixels_timeline.append(pixel_timeline)

    return {"pixels": pixels_timeline}

def main():
    # Convert carbon locations CSV to JSON
    carbon_locations_data = convert_carbon_locations_to_json('carbon_location.csv')
    with open('carbon_locations.json', 'w') as f:
        json.dump(carbon_locations_data, f, indent=2)
    
    # Convert master CSV to JSON
    master_data = convert_master_to_json('master.csv')
    with open('master.json', 'w') as f:
        json.dump(master_data, f, indent=2)

    # Create timeline JSON
    timeline_data = create_timeline_json('master.csv', 'carbon_location.csv')
    with open('timeline.json', 'w') as f:
        json.dump(timeline_data, f, indent=2)

if __name__ == "__main__":
    main() 