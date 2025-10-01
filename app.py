import pandas as pd
import numpy as np
import math
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from geopy.distance import geodesic
import folium
from folium import plugins
import uuid

app = Flask(__name__)
app.secret_key = 'school_upgrade_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Required columns for the new format
REQUIRED_COLUMNS = [
    'BemisCode', 'SchoolName', 'District', 'Tehsil', 'SubTehsil', 'UC', 
    'VillageName', 'Gender', 'SchoolLevel', 'FunctionalStatus', 
    'ReasonOfNonFunctional', 'Building', 'BuildingStructure', 'BuildingCondition',
    'SpaceForNewRooms', 'BoundaryWall', 'BoundaryWallStructure', 
    'BoundaryWallCondition', 'ElectricityInSchool', 'TotalStudentProfileEntered',
    'Source', '_xCord', '_yCord'
]

# School level hierarchy
LEVEL_HIERARCHY = {
    'Primary': 1,
    'Middle': 2,
    'High': 3,
    'Higher Secondary': 4
}

UPGRADE_MAPPING = {
    'Primary': 'Middle',
    'Middle': 'High',  
    'High': 'Higher Secondary'
}

class SchoolUpgradeAnalyzer:
    def __init__(self):
        self.schools_df = None
        self.upgrade_candidates = []
        self.search_radius_km = 25
        self.analysis_id = None
        
    def load_data(self, file_path):
        """Load and validate the uploaded CSV file"""
        try:
            # Read CSV file
            self.schools_df = pd.read_csv(file_path)
            
            # Map real data columns to expected format if needed
            if 'TotalStudentProfileEntered' not in self.schools_df.columns:
                # Try alternative column names from real data
                for alt_col in ['TotalSchoolProfileStudents', 'TotalStudents', 'Students']:
                    if alt_col in self.schools_df.columns:
                        self.schools_df['TotalStudentProfileEntered'] = self.schools_df[alt_col]
                        break
                else:
                    # Default to 50 if no student count available
                    self.schools_df['TotalStudentProfileEntered'] = 50

            # Handle coordinate columns with multiple possible names
            coord_mappings = [
                ('_xCord', ['_xCord', 'Longitude', 'longitude', 'lng', 'lon', 'x_cord', 'xCord']),
                ('_yCord', ['_yCord', 'Latitude', 'latitude', 'lat', 'y_cord', 'yCord'])
            ]
            
            for standard_name, possible_names in coord_mappings:
                if standard_name not in self.schools_df.columns:
                    found_alternative = False
                    for alt_name in possible_names:
                        if alt_name in self.schools_df.columns:
                            self.schools_df[standard_name] = self.schools_df[alt_name]
                            print(f"Mapped {alt_name} → {standard_name}")
                            found_alternative = True
                            break
                    if not found_alternative:
                        # If no coordinate column found, create default coordinates
                        print(f"Warning: No {standard_name} column found. Using default coordinates.")
                        if standard_name == '_xCord':
                            self.schools_df[standard_name] = 67.0  # Default longitude for Balochistan
                        else:
                            self.schools_df[standard_name] = 30.0  # Default latitude for Balochistan
                else:
                    print(f"Found existing {standard_name} column")

            # Clean and preprocess data - but keep ALL schools (functional and non-functional)
            self.schools_df = self.schools_df.dropna(subset=['_xCord', '_yCord'])
            self.schools_df['TotalStudentProfileEntered'] = pd.to_numeric(
                self.schools_df['TotalStudentProfileEntered'], errors='coerce'
            ).fillna(50)  # Default enrollment
            
            # Handle missing SchoolLevel data
            if 'SchoolLevel' not in self.schools_df.columns:
                self.schools_df['SchoolLevel'] = 'Primary'  # Default level
            
            # Handle missing FunctionalStatus
            if 'FunctionalStatus' not in self.schools_df.columns:
                self.schools_df['FunctionalStatus'] = 'Functional'  # Default assumption
            
            # Only filter out schools with invalid coordinates - keep all functional statuses
            self.schools_df = self.schools_df[
                (self.schools_df['_xCord'].notna()) &
                (self.schools_df['_yCord'].notna()) &
                (self.schools_df['_xCord'] != 0) &
                (self.schools_df['_yCord'] != 0)
            ]
            
            return True, f"Successfully loaded {len(self.schools_df)} schools ({self.schools_df[self.schools_df['FunctionalStatus'] == 'Functional'].shape[0]} functional, {self.schools_df[self.schools_df['FunctionalStatus'] != 'Functional'].shape[0]} non-functional)"
            
        except Exception as e:
            return False, f"Error loading file: {str(e)}"
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points"""
        try:
            return geodesic((lat1, lon1), (lat2, lon2)).kilometers
        except:
            return float('inf')
    
    def find_nearby_schools(self, target_school, target_level, radius_km):
        """Find schools of target level within radius"""
        target_lat = target_school['_yCord']
        target_lon = target_school['_xCord']
        
        # Filter schools by level and district
        level_schools = self.schools_df[
            (self.schools_df['SchoolLevel'] == target_level) &
            (self.schools_df['District'] == target_school['District'])
        ].copy()
        
        if len(level_schools) == 0:
            return level_schools
        
        # Calculate distances
        level_schools['distance'] = level_schools.apply(
            lambda row: self.calculate_distance(
                target_lat, target_lon, 
                row['_yCord'], row['_xCord']
            ), axis=1
        )
        
        # Filter by radius
        nearby_schools = level_schools[level_schools['distance'] <= radius_km]
        return nearby_schools.sort_values('distance')
    
    def find_nearby_schools_fast(self, target_school, target_level, radius_km, district_schools):
        """Fast version of find_nearby_schools for large datasets"""
        target_lat = target_school['_yCord']
        target_lon = target_school['_xCord']
        
        # Filter schools by level within district
        level_schools = district_schools[
            district_schools['SchoolLevel'] == target_level
        ].copy()
        
        if len(level_schools) == 0:
            return level_schools
        
        # Use simplified distance calculation (faster than geodesic)
        level_schools['distance'] = level_schools.apply(
            lambda row: self.calculate_distance_fast(
                target_lat, target_lon, 
                row['_yCord'], row['_xCord']
            ), axis=1
        )
        
        # Filter by radius
        nearby_schools = level_schools[level_schools['distance'] <= radius_km]
        return nearby_schools.sort_values('distance')
    
    def calculate_distance_fast(self, lat1, lon1, lat2, lon2):
        """Fast distance calculation using haversine formula"""
        try:
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            r = 6371  # Earth's radius in kilometers
            
            return c * r
        except:
            return float('inf')
    
    def analyze_upgrade_needs(self, radius_km=25, min_enrollment=20, max_candidates=500, districts=None, 
                             include_functional=True, include_non_functional=False, 
                             analyze_levels=None, genders=None):
        """Analyze schools that need upgrading - with full filtering control including gender"""
        self.search_radius_km = radius_km
        self.analysis_id = str(uuid.uuid4())
        upgrade_candidates = []
        
        print(f"Starting analysis with {len(self.schools_df)} total schools...")
        
        # Apply district filter if specified
        if districts and len(districts) > 0:
            filtered_schools = self.schools_df[self.schools_df['District'].isin(districts)].copy()
            print(f"Filtering to districts: {districts}")
        else:
            filtered_schools = self.schools_df.copy()
        
        # Apply gender filter if specified
        if genders and len(genders) > 0:
            filtered_schools = filtered_schools[filtered_schools['Gender'].isin(genders)].copy()
            print(f"Filtering to genders: {genders}")
        
        # Apply functional status filter
        functional_conditions = []
        if include_functional:
            functional_conditions.append(filtered_schools['FunctionalStatus'] == 'Functional')
        if include_non_functional:
            functional_conditions.append(filtered_schools['FunctionalStatus'] != 'Functional')
        
        if functional_conditions:
            functional_filter = functional_conditions[0]
            for condition in functional_conditions[1:]:
                functional_filter = functional_filter | condition
            filtered_schools = filtered_schools[functional_filter]
        
        print(f"After filtering: {len(filtered_schools)} schools")
        
        # Apply quality filters for functional schools only
        if include_functional:
            quality_functional = filtered_schools[
                (filtered_schools['FunctionalStatus'] == 'Functional') &
                (filtered_schools['TotalStudentProfileEntered'] >= min_enrollment) &  # Use dynamic minimum enrollment
                (~filtered_schools['BuildingCondition'].isin(['Dangerous Condition'])) &
                (filtered_schools['Building'] == 'Yes')
            ].copy()
        else:
            quality_functional = pd.DataFrame()
        
        # For non-functional schools, apply different criteria
        if include_non_functional:
            non_functional_schools = filtered_schools[
                (filtered_schools['FunctionalStatus'] != 'Functional') &
                (filtered_schools['Building'] == 'Yes')  # At least have a building
            ].copy()
        else:
            non_functional_schools = pd.DataFrame()
        
        # Combine quality schools
        quality_schools = pd.concat([quality_functional, non_functional_schools], ignore_index=True)
        
        print(f"Analyzing {len(quality_schools)} quality schools...")
        
        # Get districts to process
        districts_to_process = quality_schools['District'].unique()
        if districts and len(districts) > 0:
            districts_to_process = [d for d in districts_to_process if d in districts]
        
        # Limit districts for performance if no specific district selected
        if not districts or len(districts) == 0:
            districts_to_process = districts_to_process[:10]  # Limit to first 10 districts for demo
        
        # Set default analyze_levels if not specified
        if not analyze_levels:
            analyze_levels = list(UPGRADE_MAPPING.keys())
        
        for district_idx, district in enumerate(districts_to_process):
            print(f"Processing district {district_idx + 1}/{len(districts_to_process)}: {district}")
            
            district_schools = quality_schools[quality_schools['District'] == district]
            
            for current_level in analyze_levels:
                if current_level not in UPGRADE_MAPPING:
                    continue
                    
                next_level = UPGRADE_MAPPING[current_level]
                
                current_level_schools = district_schools[
                    district_schools['SchoolLevel'] == current_level
                ]
                
                if len(current_level_schools) == 0:
                    continue
                
                # Limit schools per level to prevent infinite loops
                sample_size = min(50, len(current_level_schools))
                sampled_schools = current_level_schools.nlargest(sample_size, 'TotalStudentProfileEntered')
                
                for _, school in sampled_schools.iterrows():
                    # Quick distance check using simplified calculation
                    nearby_higher = self.find_nearby_schools_fast(school, next_level, radius_km, district_schools)
                    
                    if len(nearby_higher) == 0:
                        # No higher level school nearby - this is a candidate
                        nearby_same_level = self.find_nearby_schools_fast(school, current_level, radius_km, district_schools)
                        
                        # Simplified criteria for upgrade recommendation
                        if (len(nearby_same_level) <= 2 or 
                            school['TotalStudentProfileEntered'] >= 
                            district_schools[district_schools['SchoolLevel'] == current_level]['TotalStudentProfileEntered'].quantile(0.7)):
                            
                            upgrade_candidates.append(self._create_candidate_record(
                                school, current_level, next_level, nearby_higher, nearby_same_level, radius_km
                            ))
                            
                            # Limit total candidates to prevent UI overload
                            if len(upgrade_candidates) >= max_candidates:
                                break
                
                if len(upgrade_candidates) >= max_candidates:
                    break
            
            if len(upgrade_candidates) >= max_candidates:
                break
        
        self.upgrade_candidates = pd.DataFrame(upgrade_candidates)
        print(f"Analysis complete. Found {len(self.upgrade_candidates)} upgrade candidates.")
        return self.upgrade_candidates
    
    def _create_candidate_record(self, school, current_level, next_level, nearby_higher, nearby_same_level, radius_km):
        """Create upgrade candidate record"""
        if len(nearby_same_level) > 1:
            reason = f'No {next_level} school within {radius_km}km, highest enrollment in area'
        else:
            reason = f'No {next_level} school within {radius_km}km, only {current_level} school in area'
        
        return {
            'BemisCode': school['BemisCode'],
            'SchoolName': school['SchoolName'],
            'District': school['District'],
            'Tehsil': school['Tehsil'],
            'SubTehsil': school['SubTehsil'],
            'UC': school['UC'],
            'VillageName': school['VillageName'],
            'Gender': school['Gender'],
            'CurrentLevel': current_level,
            'RecommendedLevel': next_level,
            'TotalStudentProfileEntered': school['TotalStudentProfileEntered'],
            'Building': school['Building'],
            'BuildingCondition': school['BuildingCondition'],
            'ElectricityInSchool': school['ElectricityInSchool'],
            'Latitude': school['_yCord'],
            'Longitude': school['_xCord'],
            'NearbyHigherSchools': len(nearby_higher),
            'NearbySameLevelSchools': len(nearby_same_level) - 1 if len(nearby_same_level) > 0 else 0,
            'UpgradeReason': reason,
            'SearchRadius_km': radius_km,
            'AnalysisDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def create_upgrade_map(self, filtered_schools_df=None):
        """Create interactive map showing filtered schools and upgrade recommendations with enhanced features"""
        # Use filtered schools if provided, otherwise use all schools
        schools_to_show = filtered_schools_df if filtered_schools_df is not None else self.schools_df
        
        if schools_to_show is None or len(schools_to_show) == 0:
            return None
        
        # Check if coordinate columns exist
        if '_yCord' not in schools_to_show.columns or '_xCord' not in schools_to_show.columns:
            print(f"Warning: Coordinate columns missing. Available columns: {list(schools_to_show.columns)}")
            return None
        
        # Calculate center point from filtered schools
        valid_coords = schools_to_show.dropna(subset=['_yCord', '_xCord'])
        if len(valid_coords) == 0:
            print("No valid coordinates found")
            return None
            
        center_lat = valid_coords['_yCord'].mean()
        center_lon = valid_coords['_xCord'].mean()
        
        # Create map with multiple tile layers
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=10,
            tiles=None,
            max_zoom=18,
            min_zoom=5
        )
        
        # Add multiple tile layers with proper attribution
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='Street Map',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite View',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Terrain Map',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Color mapping for school levels
        level_colors = {
            'Primary': '#3498db',
            'Middle': '#2ecc71', 
            'High': '#f39c12',
            'Higher Secondary': '#e74c3c'
        }
        
        # Upgrade recommendation colors (more vibrant for better visibility)
        upgrade_colors = {
            'Primary': 'red',          # Red for Primary upgrades
            'Middle': 'green',         # Green for Middle upgrades  
            'High': 'orange',          # Orange for High upgrades
            'Higher Secondary': 'purple'  # Purple for Higher Secondary upgrades
        }
        
        # Create upgrade candidates set for quick lookup
        upgrade_bemis_codes = set()
        if hasattr(self, 'upgrade_candidates') and len(self.upgrade_candidates) > 0:
            upgrade_bemis_codes = set(self.upgrade_candidates['BemisCode'].unique())
        
        # Add regular schools (smaller markers)
        for _, school in schools_to_show.iterrows():
            # Skip if coordinates are missing
            if pd.isna(school.get('_yCord')) or pd.isna(school.get('_xCord')):
                continue
            
            # Skip if this is an upgrade candidate (will be plotted separately)
            if school['BemisCode'] in upgrade_bemis_codes:
                continue
                
            color = level_colors.get(school['SchoolLevel'], '#95a5a6')
            
            popup_html = f"""
            <div style="width: 250px; font-family: 'Poppins', sans-serif;">
                <h5 style="color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                    <i class="fas fa-school"></i> {school['SchoolName']}
                </h5>
                <p><strong>BEMIS Code:</strong> {school['BemisCode']}</p>
                <p><strong>Level:</strong> <span style="color: {color}; font-weight: bold;">{school['SchoolLevel']}</span></p>
                <p><strong>District:</strong> {school['District']}</p>
                <p><strong>Tehsil:</strong> {school['Tehsil']}</p>
                <p><strong>Gender:</strong> {school['Gender']}</p>
                <p><strong>Students:</strong> {school['TotalStudentProfileEntered']}</p>
                <p><strong>Building:</strong> {school['Building']}</p>
                <p><strong>Condition:</strong> {school['BuildingCondition']}</p>
                <p><strong>Status:</strong> {school['FunctionalStatus']}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[school['_yCord'], school['_xCord']],
                radius=6,  # Smaller radius for regular schools
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{school['SchoolName']} ({school['SchoolLevel']})",
                color='white',
                weight=2,
                fill=True,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(m)
        
        # Add upgrade candidates (larger, more prominent markers)
        if hasattr(self, 'upgrade_candidates') and len(self.upgrade_candidates) > 0:
            for _, school in self.upgrade_candidates.iterrows():
                # Skip if coordinates are missing - check both coordinate naming conventions
                lat = school.get('Latitude') or school.get('_yCord')
                lon = school.get('Longitude') or school.get('_xCord')
                
                if pd.isna(lat) or pd.isna(lon):
                    continue
                    
                upgrade_color = upgrade_colors.get(school['CurrentLevel'], '#e74c3c')
                
                popup_html = f"""
                <div style="width: 300px; font-family: 'Poppins', sans-serif;">
                    <h4 style="color: #e74c3c; margin-bottom: 10px; border-bottom: 3px solid #e74c3c; padding-bottom: 5px;">
                        <i class="fas fa-arrow-up"></i> UPGRADE RECOMMENDED
                    </h4>
                    <h5 style="color: #2c3e50; margin-bottom: 10px;">
                        <i class="fas fa-school"></i> {school['SchoolName']}
                    </h5>
                    <div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <strong>Upgrade Path:</strong><br>
                        <span style="font-size: 16px; color: #721c24;">
                            {school['CurrentLevel']} → {school['RecommendedLevel']}
                        </span>
                    </div>
                    <p><strong>BEMIS Code:</strong> {school['BemisCode']}</p>
                    <p><strong>District:</strong> {school['District']}</p>
                    <p><strong>Tehsil:</strong> {school['Tehsil']}</p>
                    <p><strong>Gender:</strong> {school['Gender']}</p>
                    <p><strong>Students:</strong> {school['TotalStudentProfileEntered']}</p>
                    <p><strong>Building:</strong> {school['Building']}</p>
                    <div style="background: #fff3cd; padding: 8px; border-radius: 5px; margin-top: 10px;">
                        <strong>Reason:</strong> {school['UpgradeReason']}
                    </div>
                </div>
                """
                
                # Use a star icon for upgrade candidates with specific colors based on current level
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=f"🌟 UPGRADE: {school['SchoolName']} ({school['CurrentLevel']} → {school['RecommendedLevel']})",
                    icon=folium.Icon(
                        color=upgrade_colors.get(school['CurrentLevel'], 'red'), 
                        icon='star', 
                        prefix='fa'
                    )
                ).add_to(m)
        
        # Add enhanced legend positioned at center-left for better visibility
        legend_html = '''
        <div style="position: fixed; 
                    top: 50%; left: 20px; 
                    transform: translateY(-50%);
                    width: 300px; 
                    background-color: rgba(255, 255, 255, 0.97); 
                    border: 3px solid #2c3e50; 
                    border-radius: 15px;
                    z-index: 9999; 
                    font-size: 14px; 
                    font-family: 'Poppins', sans-serif;
                    padding: 20px;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                    backdrop-filter: blur(10px);">
        <h4 style="color: #2c3e50; margin: 0 0 15px 0; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 8px;">
            <i class="fas fa-map-marked-alt"></i> Schools & Upgrades Legend
        </h4>
        <div style="margin-bottom: 20px;">
            <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 16px;">School Levels:</h5>
            <p style="margin: 5px 0; display: flex; align-items: center;"><i class="fa fa-circle" style="color: #3498db; margin-right: 8px;"></i> Primary Schools</p>
            <p style="margin: 5px 0; display: flex; align-items: center;"><i class="fa fa-circle" style="color: #2ecc71; margin-right: 8px;"></i> Middle Schools</p>
            <p style="margin: 5px 0; display: flex; align-items: center;"><i class="fa fa-circle" style="color: #f39c12; margin-right: 8px;"></i> High Schools</p>
            <p style="margin: 5px 0; display: flex; align-items: center;"><i class="fa fa-circle" style="color: #e74c3c; margin-right: 8px;"></i> Higher Secondary</p>
        </div>
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); padding: 12px; border-radius: 8px; border: 2px solid #fdcb6e;">
            <h5 style="color: #856404; margin: 0 0 8px 0; font-size: 16px;">
                <i class="fa fa-star" style="color: #e74c3c; margin-right: 5px;"></i> Upgrade Recommended
            </h5>
            <p style="margin: 5px 0; display: flex; align-items: center; font-size: 12px;"><i class="fa fa-star" style="color: red; margin-right: 8px;"></i> Primary → Middle</p>
            <p style="margin: 5px 0; display: flex; align-items: center; font-size: 12px;"><i class="fa fa-star" style="color: green; margin-right: 8px;"></i> Middle → High</p>
            <p style="margin: 5px 0; display: flex; align-items: center; font-size: 12px;"><i class="fa fa-star" style="color: orange; margin-right: 8px;"></i> High → Higher Secondary</p>
            <p style="margin: 0; font-size: 11px; color: #856404; font-weight: 500; margin-top: 8px;">
                <strong>★ Star markers</strong> show schools recommended for upgrade
            </p>
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control for switching between map types
        folium.LayerControl().add_to(m)
        
        return m

# Global analyzer instance
analyzer = SchoolUpgradeAnalyzer()

@app.route('/')
def index():
    return render_template('index_elegant.html', required_columns=REQUIRED_COLUMNS)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Accept both CSV and Excel files
    if file and (file.filename.lower().endswith('.csv') or 
                 file.filename.lower().endswith('.xlsx') or 
                 file.filename.lower().endswith('.xls')):
        
        file.save(filepath)
        
        # Convert Excel to CSV if needed
        csv_filepath = filepath
        if filename.lower().endswith(('.xlsx', '.xls')):
            try:
                # Read Excel file and convert to CSV
                df = pd.read_excel(filepath)
                csv_filename = filename.rsplit('.', 1)[0] + '.csv'
                csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
                df.to_csv(csv_filepath, index=False)
                print(f"Converted {filename} to {csv_filename}")
            except Exception as e:
                flash(f'Error converting Excel file: {str(e)}', 'error')
                return redirect(url_for('index'))
        
        # Load and validate data
        success, message = analyzer.load_data(csv_filepath)
        
        if success:
            flash(message, 'success')
            # Prepare data for elegant configure template
            df = analyzer.schools_df
            districts = df['District'].unique().tolist()
            genders = df['Gender'].unique().tolist() if 'Gender' in df.columns else []
            levels = df['SchoolLevel'].unique().tolist() if 'SchoolLevel' in df.columns else []
            
            # Count statistics
            district_counts = df['District'].value_counts().to_dict()
            gender_counts = df['Gender'].value_counts().to_dict() if 'Gender' in df.columns else {}
            level_counts = df['SchoolLevel'].value_counts().to_dict() if 'SchoolLevel' in df.columns else {}
            functional_count = len(df[df['FunctionalStatus'] == 'Functional']) if 'FunctionalStatus' in df.columns else 0
            
            return render_template('configure_elegant.html', 
                                 total_schools=len(df),
                                 districts=sorted(districts),
                                 genders=sorted(genders),
                                 levels=sorted(levels),
                                 district_counts=district_counts,
                                 gender_counts=gender_counts,
                                 level_counts=level_counts,
                                 functional_count=functional_count,
                                 filename=filename)
        else:
            flash(message, 'error')
            return redirect(url_for('index'))
    
    else:
        flash('Invalid file type. Please upload a CSV or Excel file (.csv, .xlsx, .xls).', 'error')
        return redirect(url_for('index'))
        return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        radius = float(request.form.get('radius', 25))
        min_enrollment = int(request.form.get('min_enrollment', 20))
        
        # Get selected districts
        selected_districts = request.form.getlist('districts')
        if not selected_districts or 'all' in selected_districts:
            selected_districts = None
        
        # Get selected genders
        selected_genders = request.form.getlist('genders')
        if not selected_genders or 'all' in selected_genders:
            selected_genders = None
        
        # Get functional status preferences
        include_functional = 'functional' in request.form.getlist('functional_status')
        include_non_functional = 'non_functional' in request.form.getlist('functional_status')
        
        # If nothing selected, default to functional only
        if not include_functional and not include_non_functional:
            include_functional = True
        
        # Get school levels to analyze
        analyze_levels = request.form.getlist('analyze_levels')
        if not analyze_levels or 'all' in analyze_levels:
            analyze_levels = None
        
        if analyzer.schools_df is None:
            flash('No data loaded. Please upload a file first.', 'error')
            return redirect(url_for('index'))
        
        print(f"Analysis parameters:")
        print(f"- Radius: {radius}km")
        print(f"- Min Enrollment: {min_enrollment} students")
        print(f"- Districts: {selected_districts}")
        print(f"- Genders: {selected_genders}")
        print(f"- Include Functional: {include_functional}")
        print(f"- Include Non-Functional: {include_non_functional}")
        print(f"- Analyze Levels: {analyze_levels}")
        
        # Perform analysis
        upgrade_candidates = analyzer.analyze_upgrade_needs(
            radius_km=radius,
            min_enrollment=min_enrollment,
            districts=selected_districts,
            genders=selected_genders,
            include_functional=include_functional,
            include_non_functional=include_non_functional,
            analyze_levels=analyze_levels
        )
        
        if len(upgrade_candidates) > 0:
            # Store upgrade candidates in analyzer for map creation
            analyzer.upgrade_candidates = upgrade_candidates
            
            # Filter schools to show only from selected districts
            if selected_districts and len(selected_districts) > 0:
                # Only show schools from selected districts
                district_filtered_schools = analyzer.schools_df[analyzer.schools_df['District'].isin(selected_districts)].copy()
            else:
                # Show all schools if no specific district selected
                district_filtered_schools = analyzer.schools_df.copy()
            
            # Get BemisCodes of upgrade candidates
            upgrade_bemis_codes = set(upgrade_candidates['BemisCode'].unique())
            
            # Get districts and tehsils of upgrade candidates for context
            upgrade_locations = upgrade_candidates[['District', 'Tehsil']].drop_duplicates()
            
            # Create filter for relevant schools within selected districts:
            # 1. All upgrade candidates (should already be in selected districts)
            # 2. Schools in same tehsil as upgrade candidates
            is_upgrade_candidate = district_filtered_schools['BemisCode'].isin(upgrade_bemis_codes)
            
            # Create location filter for context schools within selected districts
            location_filter = pd.Series(False, index=district_filtered_schools.index)
            for _, loc in upgrade_locations.iterrows():
                district_match = district_filtered_schools['District'] == loc['District']
                tehsil_match = district_filtered_schools['Tehsil'] == loc['Tehsil']
                location_filter |= (district_match & tehsil_match)
            
            # Combine filters: upgrade candidates OR schools in same tehsil (within selected districts)
            filtered_schools = district_filtered_schools[is_upgrade_candidate | location_filter].copy()
            
            print(f"DEBUG: Total schools in database: {len(analyzer.schools_df)}")
            print(f"DEBUG: Schools in selected districts: {len(district_filtered_schools)}")
            print(f"DEBUG: Upgrade candidates found: {len(upgrade_candidates)}")
            print(f"DEBUG: Filtered schools for map: {len(filtered_schools)}")
            print(f"DEBUG: Selected districts: {selected_districts}")
            print(f"DEBUG: Upgrade districts/tehsils: {list(upgrade_locations.values) if not upgrade_locations.empty else 'None'}")
            
            # Limit to reasonable number for performance (max 500 schools on map)
            if len(filtered_schools) > 500:
                # Prioritize upgrade candidates first, then sample others
                upgrade_schools = filtered_schools[filtered_schools['BemisCode'].isin(upgrade_bemis_codes)]
                other_schools = filtered_schools[~filtered_schools['BemisCode'].isin(upgrade_bemis_codes)].sample(n=min(500-len(upgrade_schools), len(filtered_schools)-len(upgrade_schools)), random_state=42)
                filtered_schools = pd.concat([upgrade_schools, other_schools])
                print(f"DEBUG: Limited to {len(filtered_schools)} schools for performance")
            
            # Create map with error handling - pass filtered schools
            try:
                map_obj = analyzer.create_upgrade_map(filtered_schools)
                map_html = map_obj._repr_html_() if map_obj else None
                print(f"DEBUG: Map created successfully: {map_html is not None}")
            except Exception as map_error:
                print(f"Error creating map: {map_error}")
                import traceback
                traceback.print_exc()
                map_obj = None
                map_html = None
        else:
            filtered_schools = pd.DataFrame()  # Empty if no upgrades
            map_html = None
            
        # Calculate additional statistics for elegant template (always needed)
        upgrade_percentage = (len(upgrade_candidates) / len(analyzer.schools_df)) * 100 if len(analyzer.schools_df) > 0 else 0
        
        stats = {
            'total_schools': len(analyzer.schools_df),
            'upgrade_candidates': len(upgrade_candidates),
            'upgrade_percentage': upgrade_percentage,
            'radius_used': radius,
            'districts_analyzed': selected_districts if selected_districts else 'All',
            'genders_analyzed': selected_genders if selected_genders else 'All',
            'functional_status': f"{'Functional ' if include_functional else ''}{'Non-Functional' if include_non_functional else ''}".strip(),
            'levels_analyzed': analyze_levels if analyze_levels else 'All',
            'upgrade_breakdown': upgrade_candidates.groupby('RecommendedLevel').size().to_dict() if not upgrade_candidates.empty else {},
            'district_breakdown': upgrade_candidates['District'].value_counts().to_dict() if not upgrade_candidates.empty else {},
            'gender_breakdown': upgrade_candidates['Gender'].value_counts().to_dict() if not upgrade_candidates.empty else {}
        }
        
        # Prepare JSON data for map - only include columns that exist and only filtered schools
        required_columns = ['SchoolName', 'District', 'SchoolLevel', 'Gender', 'FunctionalStatus', '_xCord', '_yCord']
        available_columns = [col for col in required_columns if col in filtered_schools.columns]
        
        if len(available_columns) >= 5 and not filtered_schools.empty:  # At least basic info available
            rename_map = {
                'SchoolName': 'school_name',
                'SchoolLevel': 'school_level', 
                'Gender': 'school_gender',
                'FunctionalStatus': 'functional_status',
                'District': 'district'
            }
            if '_xCord' in available_columns:
                rename_map['_xCord'] = 'longitude'
            if '_yCord' in available_columns:
                rename_map['_yCord'] = 'latitude'
                
            schools_json = filtered_schools[available_columns].rename(columns=rename_map).to_json(orient='records')
        else:
            schools_json = "[]"
        
        # Prepare recommendations JSON - only include columns that exist
        rec_required_columns = ['SchoolName', 'District', 'CurrentLevel', 'RecommendedLevel', 'Gender', '_xCord', '_yCord']
        rec_available_columns = [col for col in rec_required_columns if col in upgrade_candidates.columns]
        
        if len(rec_available_columns) >= 5:  # At least basic info available
            rec_rename_map = {
                'SchoolName': 'school_name',
                'District': 'district',
                'CurrentLevel': 'current_level',
                'RecommendedLevel': 'recommended_upgrade',
                'Gender': 'school_gender'
            }
            if '_xCord' in rec_available_columns:
                rec_rename_map['_xCord'] = 'longitude'
            if '_yCord' in rec_available_columns:
                rec_rename_map['_yCord'] = 'latitude'
                
            recommendations_json = upgrade_candidates[rec_available_columns].rename(columns=rec_rename_map).to_json(orient='records')
        else:
            recommendations_json = "[]"
        
        # Prepare recommendations for template with proper column names
        def prepare_recommendations_for_template(df):
            """Convert DataFrame to list of dicts with template-friendly column names"""
            if df.empty:
                return []
            
            # Create a copy and rename columns for template use
            template_df = df.copy()
            column_mapping = {
                'SchoolName': 'school_name',
                'District': 'district',
                'CurrentLevel': 'current_level',
                'RecommendedLevel': 'recommended_upgrade',
                'Gender': 'gender',
                'TotalStudentProfileEntered': 'enrollment',
                'FunctionalStatus': 'functional_status'
            }
            
            # Only rename columns that exist
            existing_columns = {k: v for k, v in column_mapping.items() if k in template_df.columns}
            template_df = template_df.rename(columns=existing_columns)
            
            return template_df.to_dict('records')
        
        if len(upgrade_candidates) > 0:
            return render_template('results_elegant.html', 
                                 map_html=map_html,
                                 stats=stats,
                                 recommendations=prepare_recommendations_for_template(upgrade_candidates[:100]),  # Show top 100 in table
                                 schools_json=schools_json,
                                 recommendations_json=recommendations_json,
                                 analysis_id=analyzer.analysis_id)
        else:
            flash(f'No schools found that need upgrading with the specified criteria.', 'warning')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Error during analysis: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<analysis_id>')
def download_results(analysis_id):
    try:
        if analyzer.analysis_id != analysis_id or len(analyzer.upgrade_candidates) == 0:
            flash('No analysis results found or expired.', 'error')
            return redirect(url_for('index'))
        
        # Prepare download file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'school_upgrade_recommendations_{timestamp}.csv'
        filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        
        # Save results to CSV
        analyzer.upgrade_candidates.to_csv(filepath, index=False)
        
        return send_file(filepath, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='text/csv')
                        
    except Exception as e:
        flash(f'Error downloading results: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/validate_columns', methods=['POST'])
def validate_columns():
    """API endpoint to validate uploaded file columns"""
    if 'file' not in request.files:
        return jsonify({'valid': False, 'message': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'valid': False, 'message': 'No file selected'})
    
    try:
        # Read just the header
        df = pd.read_csv(file, nrows=0)
        file_columns = df.columns.tolist()
        
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in file_columns]
        extra_columns = [col for col in file_columns if col not in REQUIRED_COLUMNS]
        
        if missing_columns:
            return jsonify({
                'valid': False, 
                'message': f'Missing required columns: {", ".join(missing_columns)}',
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'file_columns': file_columns
            })
        
        return jsonify({
            'valid': True, 
            'message': 'File format is valid',
            'file_columns': file_columns,
            'extra_columns': extra_columns
        })
        
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Error reading file: {str(e)}'})

@app.route('/load-sample')
def load_sample():
    """Load the existing balochistan census data for testing"""
    try:
        # Try to load the existing data file - check multiple locations
        possible_paths = [
            'balochistan_census.csv',
            'data/balochistan_census.csv',
            os.path.join(os.path.dirname(__file__), 'balochistan_census.csv'),
            os.path.join(os.path.dirname(__file__), 'data', 'balochistan_census.csv')
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
                
        if file_path and os.path.exists(file_path):
            success, message = analyzer.load_data(file_path)
            
            if success:
                flash(f"Sample data loaded: {message}", 'success')
                # Prepare data for elegant configure template
                df = analyzer.schools_df
                districts = df['District'].unique().tolist()
                genders = df['Gender'].unique().tolist() if 'Gender' in df.columns else []
                levels = df['SchoolLevel'].unique().tolist() if 'SchoolLevel' in df.columns else []
                
                # Count statistics
                district_counts = df['District'].value_counts().to_dict()
                gender_counts = df['Gender'].value_counts().to_dict() if 'Gender' in df.columns else {}
                level_counts = df['SchoolLevel'].value_counts().to_dict() if 'SchoolLevel' in df.columns else {}
                functional_count = len(df[df['FunctionalStatus'] == 'Functional']) if 'FunctionalStatus' in df.columns else 0
                
                return render_template('configure_elegant.html', 
                                     total_schools=len(df),
                                     districts=sorted(districts)[:15],  # Limit districts shown
                                     genders=sorted(genders),
                                     levels=sorted(levels),
                                     district_counts=district_counts,
                                     gender_counts=gender_counts,
                                     level_counts=level_counts,
                                     functional_count=functional_count,
                                     filename='balochistan_census.csv')
            else:
                flash(f"Error loading sample data: {message}", 'error')
        else:
            flash("Sample data file not found", 'error')
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
    
    return redirect(url_for('index'))

@app.route('/configure')
def configure():
    """Direct access to configure page if data is already loaded"""
    if analyzer.schools_df is None or analyzer.schools_df.empty:
        flash('Please upload data first', 'warning')
        return redirect(url_for('index'))
    
    # Prepare data for elegant configure template
    df = analyzer.schools_df
    districts = df['District'].unique().tolist()
    genders = df['Gender'].unique().tolist() if 'Gender' in df.columns else []
    levels = df['SchoolLevel'].unique().tolist() if 'SchoolLevel' in df.columns else []
    
    # Count statistics
    district_counts = df['District'].value_counts().to_dict()
    gender_counts = df['Gender'].value_counts().to_dict() if 'Gender' in df.columns else {}
    level_counts = df['SchoolLevel'].value_counts().to_dict() if 'SchoolLevel' in df.columns else {}
    functional_count = len(df[df['FunctionalStatus'] == 'Functional']) if 'FunctionalStatus' in df.columns else 0
    
    return render_template('configure_elegant.html', 
                         total_schools=len(df),
                         districts=sorted(districts),
                         genders=sorted(genders),
                         levels=sorted(levels),
                         district_counts=district_counts,
                         gender_counts=gender_counts,
                         level_counts=level_counts,
                         functional_count=functional_count,
                         filename='Current Dataset')

@app.route('/ping')
def ping():
    """Simple connectivity test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'School Upgrade System is running!',
        'server_ip': request.host,
        'your_ip': request.remote_addr,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return '''
    <html>
    <head><title>System Health Check</title></head>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <h1 style="color: #2563eb;">🏫 School Upgrade System</h1>
        <h2 style="color: #059669;">✅ Server is Running!</h2>
        <p><strong>Server Time:</strong> ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        <p><strong>Your IP:</strong> ''' + request.remote_addr + '''</p>
        <p><strong>Server Host:</strong> ''' + request.host + '''</p>
        <p style="margin-top: 30px;">
            <a href="/" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Go to Main Application
            </a>
        </p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("⬆️ School Upgrade Configurator")
    print("=" * 50)
    print(f"📊 Server starting...")
    print(f"🌐 Access the application at: http://localhost:5042")
    print(f"🛑 Use Ctrl+C to stop the server")
    print("=" * 50)
    
    # Get port from environment variable (for deployment) or use default
    port = int(os.environ.get('PORT', 5042))
    
    app.run(debug=False, host='0.0.0.0', port=port)
